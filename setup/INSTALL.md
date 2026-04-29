# FOCUS ENGINE — INSTALLATION

## Prerequisites
- GitHub account
- Telegram account  
- Groq API key (free)

---

## Step 1: Get Groq API Key

1. Go to: https://console.groq.com
2. Sign up (free, no billing required)
3. API Keys → Create API Key → copy it

## Step 2: Create Telegram Bot

1. Open Telegram → message @BotFather
2. Send `/newbot` → follow prompts → copy token

## Step 3: Add GitHub Secrets

Repo → Settings → Secrets and variables → Actions → New secret:
- `GROQ_API_KEY`
- `TELEGRAM_BOT_TOKEN`

## Step 4: Initialize & Push

```bash
git clone https://github.com/penjy/focus-engine.git
cd focus-engine
pip install -r requirements.txt
git add .
git commit -m "Initialize Focus Engine"
git push
```

## Step 5: Test Locally

```bash
export GROQ_API_KEY="your_key"
export TELEGRAM_BOT_TOKEN="your_token"

python agents/focus_engine.py
cat outputs/TODAY.md
```

## Step 6: Test GitHub Action

Actions tab → "Daily Focus Engine" → "Run workflow"

Check `outputs/TODAY.md` appears in repo.

## Step 7: Deploy Telegram Bot (24/7 free)

1. Go to railway.app
2. Connect GitHub repo
3. Add env vars: `TELEGRAM_BOT_TOKEN`, `GROQ_API_KEY`
4. Set start command: `python agents/telegram_bot.py`
5. Deploy

## Verify

1. Trigger GitHub Action manually
2. Check `outputs/TODAY.md` in repo
3. Message your bot: `/focus`
4. Receive today's priorities

Done.
