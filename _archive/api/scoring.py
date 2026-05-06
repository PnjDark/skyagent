from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException
from agents.db import get_db
from groq import Groq
import os
import json

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


def _github_boost(repo: str, db) -> int:
    """Sum points from github_events in last 7 days for this repo."""
    if not repo:
        return 0
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    rows = db.table('github_events') \
        .select('points') \
        .eq('repo', repo) \
        .gte('processed_at', week_ago) \
        .execute().data
    total = sum(r['points'] for r in rows)
    return min(20, total * 20 // 200)  # 200pts = full +20 boost


def _score(p: dict, github_boost: int) -> int:
    score = {'S': 30, 'A': 25, 'B': 15, 'C': 10, 'D': 5}.get(p['tier'], 5)

    if p.get('deadline'):
        days = (datetime.fromisoformat(p['deadline']) - datetime.now()).days
        score += 20 if days < 0 else 18 if days <= 7 else 15 if days <= 14 else 10 if days <= 30 else 0

    score += {'direct': 15, 'reputation': 12, 'showcase': 8, 'community': 5, 'indirect': 6}.get(
        p.get('revenue_potential'), 0
    )

    if p.get('last_activity'):
        days = (datetime.now().date() - datetime.fromisoformat(p['last_activity']).date()).days
        score += 15 if days <= 2 else 10 if days <= 7 else 5 if days <= 14 else -20

    if 70 <= (p.get('completion') or 0) <= 90:
        score += 10

    score += p.get('priority_boost') or 0
    score += github_boost

    if p.get('status') == 'danger_zone':
        score += 15
    elif p.get('status') == 'paused':
        score -= 30

    return max(0, min(100, score))


def compute_priorities(db) -> list[dict]:
    projects = db.table('projects').select('*').not_.in_(
        'status', ['archived', 'killed']
    ).execute().data

    scored = []
    for p in projects:
        boost = _github_boost(p.get('github_repo'), db)
        scored.append({**p, 'score': _score(p, boost)})

    return sorted(scored, key=lambda x: x['score'], reverse=True)[:3]


def generate_report(priorities: list[dict], stuck: list[dict]) -> str:
    prompt = f"""You are Penjy's brutally honest Focus Engine. Tell him exactly what to work on today.

Date: {datetime.now().strftime('%B %d, %Y')}

Top 3 priorities (scored):
{json.dumps([{'name': p['id'], 'description': p['description'], 'next_milestone': p.get('next_milestone'), 'score': p['score'], 'tier': p['tier'], 'completion': p.get('completion', 0)} for p in priorities], indent=2)}

Stuck projects (14+ days no activity):
{json.dumps([{'name': p['id'], 'days_stuck': p['days_stuck'], 'completion': p.get('completion', 0)} for p in stuck], indent=2)}

Voice: direct, no fluff, slightly aggressive honesty, celebrates momentum, calls out avoidance.

Format exactly:
🎯 FOCUS FOR TODAY — [Date]

**Top Priority:**
1. [Project]: [Specific task] ([time]) → [WHY IT MATTERS]

**Secondary:**
2. [Project]: [Task] ([time]) → [IMPACT]
3. [Project]: [Task] ([time]) → [VALUE]

⚠️ **Warnings:**
- [stuck projects / dangerous patterns]

📊 **This Week Goal:** [Strategic objective]

**Brutal Truth:**
[One line of hard honesty]

Max 200 words."""

    return _get_groq_client().chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}]
    ).choices[0].message.content


@router.post('/run')
def run_scoring():
    db = get_db()

    priorities = compute_priorities(db)

    # Find stuck projects
    all_projects = db.table('projects').select('*').eq('status', 'active').execute().data
    stuck = []
    for p in all_projects:
        if p.get('last_activity'):
            days = (datetime.now().date() - datetime.fromisoformat(p['last_activity']).date()).days
            if days > 14:
                stuck.append({**p, 'days_stuck': days})

    report = generate_report(priorities, stuck)

    today = datetime.now(timezone.utc).date().isoformat()
    db.table('daily_priorities').upsert({
        'date': today,
        'content': report,
        'priorities': [{'name': p['id'], 'score': p['score'], 'tier': p['tier']} for p in priorities],
    }, on_conflict='date').execute()

    return {'status': 'ok', 'date': today, 'report': report}
