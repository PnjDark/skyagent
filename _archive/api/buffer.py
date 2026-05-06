import os
import httpx
from fastapi import APIRouter, HTTPException
from agents.db import get_db

router = APIRouter()

BUFFER_API = 'https://api.buffer.com'
BUFFER_TOKEN = os.environ.get('BUFFER_ACCESS_TOKEN', '')

HEADERS = {
    'Authorization': f'Bearer {BUFFER_TOKEN}',
    'Content-Type': 'application/json',
}

CREATE_POST = """
mutation CreatePost($text: String!, $channelId: String!, $saveToDraft: Boolean!) {
  createPost(input: {
    text: $text,
    channelId: $channelId,
    schedulingType: automatic,
    mode: addToQueue,
    saveToDraft: $saveToDraft
  }) {
    ... on PostActionSuccess {
      post { id text }
    }
    ... on MutationError {
      message
    }
  }
}
"""

GET_CHANNELS = """
query {
  channels {
    id
    service
    name
  }
}
"""


async def _gql(query: str, variables: dict = None) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            BUFFER_API,
            headers=HEADERS,
            json={'query': query, 'variables': variables or {}},
            timeout=30,
        )
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f'Buffer API error: {r.text}')
    body = r.json()
    if 'errors' in body:
        raise HTTPException(status_code=502, detail=f'Buffer GraphQL error: {body["errors"]}')
    return body['data']


async def _get_channels() -> dict[str, str]:
    """Returns {service: channel_id} for linkedin and twitter."""
    data = await _gql(GET_CHANNELS)
    channels = {}
    for ch in data.get('channels', []):
        service = ch.get('service', '').lower()
        if service in ('linkedin', 'twitter') and service not in channels:
            channels[service] = ch['id']
    return channels


async def schedule_draft(draft_id: int, save_as_draft: bool = False) -> dict:
    db = get_db()

    rows = db.table('content_drafts').select('*').eq('id', draft_id).execute().data
    if not rows:
        raise HTTPException(status_code=404, detail='Draft not found')
    draft = rows[0]

    if draft['status'] not in ('approved', 'pending'):
        raise HTTPException(status_code=400, detail=f"Draft status is '{draft['status']}', cannot schedule")

    channels = await _get_channels()
    post_ids = {}

    if draft.get('linkedin_draft') and 'linkedin' in channels:
        data = await _gql(CREATE_POST, {
            'text': draft['linkedin_draft'],
            'channelId': channels['linkedin'],
            'saveToDraft': save_as_draft,
        })
        result = data.get('createPost', {})
        if 'post' in result:
            post_ids['linkedin'] = result['post']['id']
        elif 'message' in result:
            raise HTTPException(status_code=502, detail=f'LinkedIn post failed: {result["message"]}')

    if draft.get('x_draft') and 'twitter' in channels:
        data = await _gql(CREATE_POST, {
            'text': draft['x_draft'],
            'channelId': channels['twitter'],
            'saveToDraft': save_as_draft,
        })
        result = data.get('createPost', {})
        if 'post' in result:
            post_ids['twitter'] = result['post']['id']
        elif 'message' in result:
            raise HTTPException(status_code=502, detail=f'X post failed: {result["message"]}')

    if not post_ids:
        raise HTTPException(status_code=400, detail='No matching Buffer channels found for linkedin/twitter')

    db.table('content_drafts').update({
        'status': 'scheduled',
        'approved_at': __import__('datetime').datetime.utcnow().isoformat(),
        'buffer_post_ids': post_ids,
    }).eq('id', draft_id).execute()

    return {'draft_id': draft_id, 'scheduled_to': list(post_ids.keys()), 'buffer_ids': post_ids}


@router.post('/schedule/{draft_id}')
async def schedule_endpoint(draft_id: int):
    return await schedule_draft(draft_id)


@router.post('/draft/{draft_id}')
async def save_as_draft_endpoint(draft_id: int):
    """Save to Buffer as draft instead of queuing."""
    return await schedule_draft(draft_id, save_as_draft=True)
