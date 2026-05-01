import os
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from groq import Groq

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.db import get_db

client = Groq(api_key=os.environ['GROQ_API_KEY'])


def generate_weekly_review():
    db = get_db()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()

    logs = db.table('project_logs').select('*').gte('date', week_ago).execute().data
    projects = db.table('projects').select('*').execute().data

    week_data = {}
    for log in logs:
        week_data.setdefault(log['date'], {})[log['project_id']] = log['achievement']

    prompt = f"""Generate a weekly review for Penjy.

This week's activity:
{json.dumps(week_data, indent=2)}

Current project status:
{json.dumps([{'id': p['id'], 'tier': p['tier'], 'status': p['status'], 'completion': p.get('completion', 0), 'last_activity': p.get('last_activity')} for p in projects], indent=2)}

Format:
📊 WEEKLY REVIEW — [Date Range]

🚀 SHIPPED:
[What got done, grouped by tier]

⏳ IN PROGRESS:
[Active projects with completion %]

❌ STALLED:
[Projects with no activity]

💰 REVENUE OPPORTUNITIES:
[Money-making progress insights]

🎯 NEXT WEEK PRIORITY:
[Strategic focus]

**Reality Check:**
[Brutally honest — 2 sentences max]

Under 300 words. Be direct."""

    report = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}]
    ).choices[0].message.content

    # Store in daily_priorities table with a weekly flag
    db.table('daily_priorities').upsert({
        'date': datetime.now(timezone.utc).date().isoformat(),
        'content': report,
        'priorities': [],
    }, on_conflict='date').execute()

    print('✅ Weekly review generated')
    return report


if __name__ == '__main__':
    generate_weekly_review()
