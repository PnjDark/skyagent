import json
import os
from datetime import datetime, timedelta
from groq import Groq

client = Groq(api_key=os.environ['GROQ_API_KEY'])


def generate_weekly_review():
    with open('data/project_status.json') as f:
        status = json.load(f)
    with open('data/projects.json') as f:
        projects = json.load(f)

    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_data = {k: v for k, v in status.items() if k >= week_ago}

    prompt = f"""Generate a weekly review for Penjy.

This week's activity:
{json.dumps(week_data, indent=2)}

Current project status:
{json.dumps(projects, indent=2)}

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

    os.makedirs('outputs', exist_ok=True)
    with open('outputs/WEEKLY_REVIEW.md', 'w') as f:
        f.write(report)

    print("✅ Weekly review generated")
    return report


if __name__ == '__main__':
    generate_weekly_review()
