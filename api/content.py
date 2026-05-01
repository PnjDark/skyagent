import os
import json
from fastapi import APIRouter, HTTPException
from groq import Groq
from agents.db import get_db

router = APIRouter()
client = None


def _get_groq_client():
    global client
    if client is None:
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail='GROQ_API_KEY is not set')
        client = Groq(api_key=api_key)
    return client

DRAFT_EVENTS = {'release', 'pr_merged', 'repo_publicized', 'repo_created'}


async def generate_draft(event_id: int, repo: str, event_type: str, payload: dict):
    if event_type not in DRAFT_EVENTS:
        return

    db = get_db()

    # Find linked project
    project_rows = db.table('projects').select('*').eq('github_repo', repo).execute().data
    project = project_rows[0] if project_rows else {'id': repo, 'description': repo}

    event_summary = {
        'release': f"Released {payload.get('release', {}).get('name', 'new version')}",
        'pr_merged': f"Merged: {payload.get('pull_request', {}).get('title', 'a pull request')}",
        'repo_publicized': f"Made {repo} public",
        'repo_created': f"Created new repo {repo}",
    }.get(event_type, event_type)

    prompt = f"""You are a developer brand copywriter for Penjy, a builder from Cameroon.

Event: {event_summary}
Project: {project['id']} — {project.get('description', '')}

Write two posts:

LINKEDIN (3-4 sentences, professional, shows momentum, ends with insight or question):

X (under 240 chars, punchy, no hashtag spam, max 2 relevant tags):

Also write one sentence to update the portfolio card description for this project.

Return as JSON:
{{"linkedin": "...", "x": "...", "portfolio_update": "..."}}"""

    response = _get_groq_client().chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}],
        response_format={'type': 'json_object'},
    ).choices[0].message.content

    drafts = json.loads(response)

    db.table('content_drafts').insert({
        'project_id': project['id'],
        'github_event_id': event_id,
        'linkedin_draft': drafts.get('linkedin'),
        'x_draft': drafts.get('x'),
        'portfolio_update': drafts.get('portfolio_update'),
        'status': 'pending',
    }).execute()

    # Also add to portfolio feed
    db.table('portfolio_feed').insert({
        'project_id': project['id'],
        'event_type': event_type,
        'summary': event_summary,
        'date': __import__('datetime').date.today().isoformat(),
        'type': 'launch' if event_type in ('release', 'repo_publicized') else 'update',
        'github_event_id': event_id,
    }).execute()


@router.get('/drafts')
def list_drafts():
    db = get_db()
    rows = db.table('content_drafts').select('*, projects(id, description)') \
        .eq('status', 'pending').order('created_at', desc=True).execute().data
    return rows


@router.post('/drafts/{draft_id}/approve')
async def approve_draft(draft_id: int):
    db = get_db()
    db.table('content_drafts').update({'status': 'approved'}).eq('id', draft_id).execute()

    # Immediately schedule to Buffer
    from api.buffer import schedule_draft
    result = await schedule_draft(draft_id)
    return {'status': 'scheduled', 'draft_id': draft_id, 'buffer': result}


@router.post('/drafts/{draft_id}/reject')
def reject_draft(draft_id: int):
    db = get_db()
    db.table('content_drafts').update({'status': 'rejected'}).eq('id', draft_id).execute()
    return {'status': 'rejected', 'draft_id': draft_id}
