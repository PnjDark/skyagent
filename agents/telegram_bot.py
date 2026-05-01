import os
import sys
from pathlib import Path
import httpx
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.db import get_db

TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
RAILWAY_URL = os.environ.get('RAILWAY_URL', 'http://localhost:8000')


# ── helpers ──────────────────────────────────────────────────────────────────

def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()

def days_since(date_str: str) -> int:
    return (datetime.now().date() - datetime.fromisoformat(date_str).date()).days


# ── commands ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 Focus Engine\n\n"
        "/focus — Today's priorities\n"
        "/generate — Regenerate focus\n"
        "/done <project> <what you did> — Log progress\n"
        "/status — Project health dashboard\n"
        "/wins — Recent GitHub-backed wins\n"
        "/activity — Repo activity summary\n"
        "/ghost — Check if you've gone quiet\n"
        "/drafts — Content drafts waiting for approval\n"
        "/schedule <id> — Send approved draft to Buffer"
    )


async def focus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    row = db.table('daily_priorities').select('content').eq('date', today()).execute().data
    if row:
        await update.message.reply_text(row[0]['content'], parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ No focus for today yet. Run /generate.")


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Generating focus report...")
    async with httpx.AsyncClient() as client:
        r = await client.post(f'{RAILWAY_URL}/scoring/run', timeout=60)
    if r.status_code == 200:
        report = r.json().get('report', '')
        await update.message.reply_text(f"✅ Generated!\n\n{report}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ Error: {r.text}")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /done <project_name> <what you did>")
        return

    project_id = context.args[0]
    achievement = ' '.join(context.args[1:])
    db = get_db()

    # Verify project exists
    exists = db.table('projects').select('id').eq('id', project_id).execute().data
    if not exists:
        await update.message.reply_text(f"⚠️ Project '{project_id}' not found. Check /status for names.")
        return

    db.table('project_logs').insert({
        'date': today(),
        'project_id': project_id,
        'achievement': achievement,
    }).execute()

    db.table('projects').update({
        'last_activity': today()
    }).eq('id', project_id).execute()

    await update.message.reply_text(
        f"🎉 Logged: {project_id} → {achievement}\n\nMomentum maintained. Keep shipping."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    projects = db.table('projects').select('id, status, completion, last_activity, tier').execute().data

    active  = [p for p in projects if p['status'] == 'active']
    danger  = [p for p in projects if p['status'] == 'danger_zone']
    paused  = [p for p in projects if p['status'] == 'paused']

    lines = ["📊 PROJECT HEALTH\n"]
    lines.append(f"🟢 Active: {len(active)}  🔴 Danger: {len(danger)}  ⏸ Paused: {len(paused)}\n")

    if danger:
        lines.append("🔴 Danger Zone:")
        for p in danger:
            days = days_since(p['last_activity']) if p.get('last_activity') else '?'
            lines.append(f"  • {p['id']} ({p['completion']}% done, {days}d silent)")

    if active:
        lines.append("\n🟢 Active:")
        for p in sorted(active, key=lambda x: x.get('completion', 0), reverse=True):
            days = days_since(p['last_activity']) if p.get('last_activity') else '?'
            lines.append(f"  • {p['id']} [{p['tier']}] {p['completion']}% — {days}d ago")

    await update.message.reply_text('\n'.join(lines))


async def wins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    events = db.table('github_events') \
        .select('repo, event_type, points, processed_at') \
        .in_('event_type', ['release', 'pr_merged', 'push_main', 'repo_publicized']) \
        .order('processed_at', desc=True) \
        .limit(10).execute().data

    if not events:
        await update.message.reply_text("No wins tracked yet. Start shipping.")
        return

    lines = ["🏆 RECENT WINS\n"]
    for e in events:
        date = e['processed_at'][:10]
        lines.append(f"• {e['repo']} — {e['event_type']} (+{e['points']}pts) [{date}]")

    await update.message.reply_text('\n'.join(lines))


async def activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    events = db.table('github_events') \
        .select('repo, points') \
        .gte('processed_at', week_ago).execute().data

    if not events:
        await update.message.reply_text("No GitHub activity in the last 7 days.")
        return

    totals: dict[str, int] = {}
    for e in events:
        totals[e['repo']] = totals.get(e['repo'], 0) + e['points']

    lines = ["📈 GITHUB ACTIVITY (last 7 days)\n"]
    for repo, pts in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        bar = '█' * min(10, pts // 20)
        boost = f"+{min(20, pts * 20 // 200)}pts boost" if pts >= 10 else "no boost yet"
        lines.append(f"• {repo}: {pts}pts {bar} ({boost})")

    await update.message.reply_text('\n'.join(lines))


async def ghost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()

    events = db.table('github_events') \
        .select('points') \
        .gte('processed_at', week_ago).execute().data

    total = sum(e['points'] for e in events)

    if total < 50:
        await update.message.reply_text(
            f"👻 GHOST ALERT\n\nOnly {total}pts in the last 5 days.\n"
            "You've gone quiet. What are you avoiding?"
        )
    else:
        await update.message.reply_text(
            f"✅ You're alive — {total}pts in the last 5 days. Keep it up."
        )


async def drafts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    rows = db.table('content_drafts') \
        .select('id, project_id, linkedin_draft, x_draft, created_at') \
        .eq('status', 'pending') \
        .order('created_at', desc=True) \
        .limit(5).execute().data

    if not rows:
        await update.message.reply_text("No pending drafts. Keep shipping to generate some.")
        return

    lines = ["✍️ PENDING DRAFTS\n"]
    for d in rows:
        lines.append(f"ID {d['id']} — {d['project_id']} ({d['created_at'][:10]})")
        lines.append(f"  LinkedIn: {d['linkedin_draft'][:80]}...")
        lines.append(f"  X: {d['x_draft'][:80]}...")
        lines.append(f"  → /schedule {d['id']} to approve & queue\n")

    await update.message.reply_text('\n'.join(lines))


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /schedule <draft_id>")
        return

    draft_id = context.args[0]
    async with httpx.AsyncClient() as client:
        r = await client.post(f'{RAILWAY_URL}/content/drafts/{draft_id}/approve', timeout=30)

    if r.status_code == 200:
        data = r.json()
        platforms = ', '.join(data.get('buffer', {}).get('scheduled_to', []))
        await update.message.reply_text(
            f"✅ Draft {draft_id} queued on Buffer\n"
            f"Platforms: {platforms or 'unknown'}\n"
            f"It will post at your next scheduled Buffer slot."
        )
    else:
        await update.message.reply_text(f"❌ Buffer error: {r.text}")


# ── app ───────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()
    for cmd, fn in [
        ('start',    start),
        ('focus',    focus),
        ('generate', generate),
        ('done',     done),
        ('status',   status),
        ('wins',     wins),
        ('activity', activity),
        ('ghost',    ghost),
        ('drafts',   drafts),
        ('schedule', schedule),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    print("🤖 Telegram bot running...")
    app.run_polling()


if __name__ == '__main__':
    main()
