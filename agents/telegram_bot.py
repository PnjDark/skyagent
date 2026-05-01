import os
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

TOKEN = os.environ['TELEGRAM_BOT_TOKEN']


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 Penjy Focus Engine\n\n"
        "/focus — Today's priorities\n"
        "/generate — Manually generate focus\n"
        "/done <project> <achievement> — Log progress\n"
        "/status — Project health dashboard"
    )


async def focus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open('outputs/TODAY.md') as f:
            await update.message.reply_text(f.read(), parse_mode='Markdown')
    except FileNotFoundError:
        await update.message.reply_text("⚠️ No focus generated yet. Run /generate first.")


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Generating focus report...")
    result = subprocess.run(['python', 'agents/focus_engine.py'], capture_output=True, text=True)
    if result.returncode == 0:
        with open('outputs/TODAY.md') as f:
            await update.message.reply_text(f"✅ Generated!\n\n{f.read()}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ Error:\n{result.stderr}")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /done <project_name> <what you did>")
        return

    project = context.args[0]
    achievement = ' '.join(context.args[1:])
    date_key = datetime.now().strftime('%Y-%m-%d')

    # Update project_status.json
    try:
        with open('data/project_status.json') as f:
            status = json.load(f)
    except FileNotFoundError:
        status = {}

    status.setdefault(date_key, {})[project] = achievement
    with open('data/project_status.json', 'w') as f:
        json.dump(status, f, indent=2)

    # Update last_activity in projects.json
    try:
        with open('data/projects.json') as f:
            projects = json.load(f)
        if project in projects:
            projects[project]['last_activity'] = datetime.now().strftime('%Y-%m-%d')
            with open('data/projects.json', 'w') as f:
                json.dump(projects, f, indent=2)
    except FileNotFoundError:
        pass

    await update.message.reply_text(
        f"🎉 Logged: {project} → {achievement}\n\nMomentum maintained. Keep shipping."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('data/projects.json') as f:
        projects = json.load(f)

    active = [k for k, v in projects.items() if v.get('status') == 'active']
    danger = [k for k, v in projects.items() if v.get('status') == 'danger_zone']

    msg = (
        f"📊 PROJECT HEALTH\n\n"
        f"🟢 Active: {len(active)}\n"
        f"🔴 Danger Zone: {len(danger)}\n\n"
        f"Stuck projects:\n"
        f"{chr(10).join(f'- {p}' for p in danger) if danger else 'None'}\n\n"
        f"Run /focus for today's priorities."
    )
    await update.message.reply_text(msg)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("focus", focus))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("status", status))
    print("🤖 Telegram bot running...")
    app.run_polling()


if __name__ == '__main__':
    main()
