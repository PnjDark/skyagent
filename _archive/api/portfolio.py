from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

from agents.db import get_db

router = APIRouter()

HIDDEN_PROJECT_STATUSES = {'archived', 'killed'}


def _clean_project(project: dict[str, Any]) -> dict[str, Any]:
    return {
        'id': project.get('id'),
        'title': project.get('id'),
        'tier': project.get('tier'),
        'status': project.get('status'),
        'category': project.get('category'),
        'description': project.get('description'),
        'next_milestone': project.get('next_milestone'),
        'completion': project.get('completion') or 0,
        'github_repo': project.get('github_repo'),
        'github_url': f"https://github.com/{project['github_repo']}" if project.get('github_repo') else None,
        'last_activity': project.get('last_activity'),
    }


def _clean_activity(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'id': item.get('id'),
        'project_id': item.get('project_id'),
        'event_type': item.get('event_type'),
        'summary': item.get('summary'),
        'date': item.get('date'),
        'type': item.get('type') or 'update',
    }


@router.get('/feed')
def portfolio_feed(limit: int = Query(default=30, ge=1, le=100)):
    db = get_db()

    projects = db.table('projects') \
        .select('id, tier, status, category, description, next_milestone, completion, github_repo, last_activity') \
        .order('tier') \
        .execute().data

    activity = db.table('portfolio_feed') \
        .select('id, project_id, event_type, summary, date, type') \
        .order('date', desc=True) \
        .limit(limit) \
        .execute().data

    visible_projects = [
        _clean_project(project)
        for project in projects
        if project.get('status') not in HIDDEN_PROJECT_STATUSES
    ]

    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'projects': visible_projects,
        'recent_activity': [_clean_activity(item) for item in activity],
    }
