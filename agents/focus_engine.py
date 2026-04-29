import json
import os
from datetime import datetime
from groq import Groq

client = Groq(api_key=os.environ['GROQ_API_KEY'])


class FocusEngine:
    def __init__(self):
        self.projects = self._load('data/projects.json')
        self.history = self._load('data/focus_history.json')

    def _load(self, path):
        try:
            with open(path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _score(self, project):
        score = {'S': 30, 'A': 25, 'B': 15, 'C': 10, 'D': 5}.get(project['tier'], 5)

        if project.get('deadline'):
            days = (datetime.fromisoformat(project['deadline']) - datetime.now()).days
            score += 20 if days < 0 else 18 if days <= 7 else 15 if days <= 14 else 10 if days <= 30 else 0

        score += {'direct': 15, 'reputation': 12, 'showcase': 8, 'community': 5, 'indirect': 6}.get(
            project.get('revenue_potential'), 0
        )

        if project.get('last_activity'):
            days = (datetime.now() - datetime.fromisoformat(project['last_activity'])).days
            score += 15 if days <= 2 else 10 if days <= 7 else 5 if days <= 14 else -20

        if 70 <= project.get('completion', 0) <= 90:
            score += 10

        score += project.get('priority_boost', 0)

        if project.get('status') == 'danger_zone':
            score += 15
        elif project.get('status') == 'paused':
            score -= 30

        return max(0, min(100, score))

    def top_priorities(self, limit=3):
        scored = [
            (key, proj, self._score(proj))
            for key, proj in self.projects.items()
            if proj.get('status') not in ['archived', 'killed']
        ]
        return sorted(scored, key=lambda x: x[2], reverse=True)[:limit]

    def stuck_projects(self, threshold=14):
        result = []
        for key, proj in self.projects.items():
            if proj.get('status') == 'active' and proj.get('last_activity'):
                days = (datetime.now() - datetime.fromisoformat(proj['last_activity'])).days
                if days > threshold:
                    result.append((key, proj, days))
        return result

    def generate_report(self):
        priorities = self.top_priorities()
        stuck = self.stuck_projects()

        prompt = f"""You are Penjy's brutally honest Focus Engine. Tell him exactly what to work on today.

Date: {datetime.now().strftime('%B %d, %Y')}

Top 3 priorities (scored):
{json.dumps([{'name': k, 'description': p['description'], 'next_milestone': p.get('next_milestone'), 'score': s, 'tier': p['tier'], 'completion': p.get('completion', 0)} for k, p, s in priorities], indent=2)}

Stuck projects (14+ days no activity):
{json.dumps([{'name': k, 'days_stuck': d, 'completion': p.get('completion', 0)} for k, p, d in stuck], indent=2)}

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

        return client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}]
        ).choices[0].message.content

    def run(self):
        print("🧠 Focus Engine starting...")
        report = self.generate_report()

        os.makedirs('outputs', exist_ok=True)
        with open('outputs/TODAY.md', 'w') as f:
            f.write(report)

        date_key = datetime.now().strftime('%Y-%m-%d')
        self.history[date_key] = {'content': report, 'generated_at': datetime.now().isoformat()}
        self._save('data/focus_history.json', self.history)

        print("✅ TODAY.md generated\n")
        print(report)
        return report


if __name__ == '__main__':
    FocusEngine().run()
