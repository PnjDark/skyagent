import hashlib
import hmac
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request
from agents.db import get_db

router = APIRouter()

# Points per event type (mirrors README scoring)
EVENT_POINTS = {
    'push_main':      lambda commits: 30 + 5 * commits,
    'push_branch':    lambda commits: 10 + 2 * commits,
    'release':        90,
    'pr_merged':      70,
    'pr_opened':      20,
    'issue_closed':   15,
    'fork':           10,
    'star':            5,
    'repo_created':   25,
    'repo_publicized': 40,
}

def _importance(points: int) -> str:
    if points >= 70: return 'high'
    if points >= 20: return 'medium'
    return 'low'

def _verify_signature(body: bytes, sig: str) -> bool:
    secret = os.environ.get('GITHUB_WEBHOOK_SECRET', '')
    expected = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig or '')

def _score_event(event_type: str, payload: dict) -> tuple[str, int]:
    """Returns (internal_event_type, points)"""
    if event_type == 'push':
        branch = payload.get('ref', '')
        commits = len(payload.get('commits', []))
        if 'main' in branch or 'master' in branch:
            return 'push_main', EVENT_POINTS['push_main'](commits)
        return 'push_branch', EVENT_POINTS['push_branch'](commits)

    if event_type == 'release' and payload.get('action') == 'published':
        return 'release', EVENT_POINTS['release']

    if event_type == 'pull_request':
        action = payload.get('action')
        if action == 'closed' and payload.get('pull_request', {}).get('merged'):
            return 'pr_merged', EVENT_POINTS['pr_merged']
        if action == 'opened':
            return 'pr_opened', EVENT_POINTS['pr_opened']

    if event_type == 'issues' and payload.get('action') == 'closed':
        return 'issue_closed', EVENT_POINTS['issue_closed']

    if event_type == 'fork':
        return 'fork', EVENT_POINTS['fork']

    if event_type == 'star' and payload.get('action') == 'created':
        return 'star', EVENT_POINTS['star']

    if event_type == 'repository':
        action = payload.get('action')
        if action == 'created':
            return 'repo_created', EVENT_POINTS['repo_created']
        if action == 'publicized':
            return 'repo_publicized', EVENT_POINTS['repo_publicized']

    return event_type, 0


@router.post('/github')
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
):
    body = await request.body()
    if not _verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail='Invalid signature')

    payload = await request.json()
    repo = payload.get('repository', {}).get('full_name', 'unknown')

    internal_type, points = _score_event(x_github_event, payload)
    if points == 0:
        return {'status': 'ignored'}

    db = get_db()

    # Write event
    event_row = db.table('github_events').insert({
        'repo': repo,
        'event_type': internal_type,
        'payload': payload,
        'importance': _importance(points),
        'points': points,
    }).execute().data[0]

    # Update project last_activity if repo is linked
    db.table('projects').update({
        'last_activity': datetime.now(timezone.utc).date().isoformat()
    }).eq('github_repo', repo).execute()

    # Trigger content draft for high-importance events
    if _importance(points) == 'high':
        from api.content import generate_draft
        await generate_draft(event_row['id'], repo, internal_type, payload)

    return {'status': 'ok', 'event': internal_type, 'points': points}
