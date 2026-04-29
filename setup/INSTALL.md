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

## Step 3: Generate a Webhook Secret

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Save the output — you'll use it as `GITHUB_WEBHOOK_SECRET`.

## Step 4: Create a GitHub Personal Access Token

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → scopes: `repo`, `read:user`
3. Copy the token

## Step 5: Configure Environment Variables

**For local use**, create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_groq_key
TELEGRAM_BOT_TOKEN=your_telegram_token
GITHUB_TOKEN=your_github_pat
GITHUB_USERNAME=your_github_username
GITHUB_WEBHOOK_SECRET=your_generated_secret
```

**For GitHub Actions**, add secrets in repo → Settings → Secrets and variables → Actions:
- `GROQ_API_KEY`
- `TELEGRAM_BOT_TOKEN`

## Step 6: Install & Test Locally

```bash
git clone https://github.com/penjy/focus-engine.git
cd focus-engine
pip install -r requirements.txt

# Test focus engine
python agents/focus_engine.py
cat outputs/TODAY.md

# Test webhook server
uvicorn api.main:app --reload
# Visit http://localhost:8000/health
```

## Step 7: Deploy to Railway

1. Go to railway.app → New Project → Deploy from GitHub repo
2. Railway will detect the `Procfile` and run both processes automatically:
   - `web` — FastAPI webhook server (public URL)
   - `worker` — Telegram bot (polling)
3. Add all environment variables in Railway dashboard:
   - `GROQ_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `GITHUB_TOKEN`
   - `GITHUB_USERNAME`
   - `GITHUB_WEBHOOK_SECRET`
4. After deploy, copy your Railway public URL (e.g. `https://your-app.up.railway.app`)

## Step 8: Configure GitHub Webhooks

For each repo you want to track (repeat per project):

1. Repo → Settings → Webhooks → Add webhook
2. Fill in:
   - **Payload URL**: `https://your-app.up.railway.app/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: your `GITHUB_WEBHOOK_SECRET`
3. Under "Which events?", select **Let me select individual events** and check:
   - ✅ Pushes
   - ✅ Pull requests
   - ✅ Releases
   - ✅ Issues
   - ✅ Stars
   - ✅ Forks
4. Click **Add webhook** — GitHub will send a ping and show a green checkmark

## Step 9: Verify Everything

```bash
# 1. Trigger a GitHub Action manually
# Actions tab → "Daily Focus Engine" → Run workflow
# Check outputs/TODAY.md appears in repo

# 2. Test the webhook
# Make a commit to any tracked repo, then in Telegram:
/wins       # should show the commit
/activity   # should show score > 0

# 3. Test bot commands
/focus      # today's priorities
/status     # project health
/ghost      # activity check
```

Done.
