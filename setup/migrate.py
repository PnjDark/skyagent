"""
Phase 1 migration: JSON files → Supabase
Run once: python setup/migrate.py
"""
import json
import os
from datetime import datetime
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def migrate_projects():
    projects = load('data/projects.json')
    rows = []
    for pid, p in projects.items():
        rows.append({
            'id': pid,
            'tier': p['tier'],
            'status': p['status'],
            'category': p.get('category'),
            'revenue_potential': p.get('revenue_potential'),
            'completion': p.get('completion', 0),
            'last_activity': p.get('last_activity'),
            'deadline': p.get('deadline'),
            'priority_boost': p.get('priority_boost', 0),
            'description': p.get('description'),
            'next_milestone': p.get('next_milestone'),
            'github_repo': p.get('github_repo'),
        })
    sb.table('projects').upsert(rows).execute()
    print(f"✅ Migrated {len(rows)} projects")


def migrate_focus_history():
    history = load('data/focus_history.json')
    rows = []
    for date_key, entry in history.items():
        rows.append({
            'date': date_key,
            'content': entry['content'],
            'generated_at': entry.get('generated_at', datetime.now().isoformat()),
        })
    if rows:
        sb.table('daily_priorities').upsert(rows, on_conflict='date').execute()
    print(f"✅ Migrated {len(rows)} focus history entries")


def migrate_project_logs():
    status = load('data/project_status.json')
    rows = []
    for date_key, projects in status.items():
        for project_id, achievement in projects.items():
            rows.append({
                'date': date_key,
                'project_id': project_id,
                'achievement': achievement,
            })
    if rows:
        sb.table('project_logs').insert(rows).execute()
    print(f"✅ Migrated {len(rows)} project logs")


if __name__ == '__main__':
    print("🚀 Starting migration to Supabase...")
    migrate_projects()
    migrate_focus_history()
    migrate_project_logs()
    print("\n✅ Migration complete. Verify in your Supabase dashboard.")
