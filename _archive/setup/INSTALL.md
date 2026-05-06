# Focus Engine — Installation Guide

## What you need accounts for

| Service | Purpose | Cost |
|---------|---------|------|
| Supabase | Database | Free tier |
| Railway | Backend + Telegram bot | Free tier |
| Vercel | Dashboard | Free tier |
| Groq | AI (Llama) | Free tier |
| Telegram | Bot | Free |
| Buffer | Social scheduling | Free tier |
| GitHub | Source of truth | Free |

---

## Phase 1 — Database (Supabase)

### 1.1 Create project

1. Go to [supabase.com](https://supabase.com) → New project
2. Settings → API → copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`

### 1.2 Run schema

1. Supabase dashboard → SQL Editor
2. Paste contents of `setup/schema.sql` → Run

### 1.3 Migrate existing data

If you have existing JSON data, run the migration from Railway after deploying (Phase 2):

```bash
python setup/migrate.py
```

---

## Phase 2 — Backend (Railway)

### 2.1 Deploy

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Railway detects the `Procfile` and runs:
   - `web` — FastAPI server (public URL, handles webhooks + API)
   - `worker` — Telegram bot (polling)

### 2.2 Set environment variables

In Railway dashboard → your service → Variables:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GROQ_API_KEY=your-groq-key
TELEGRAM_BOT_TOKEN=your-telegram-token
GITHUB_WEBHOOK_SECRET=your-generated-secret
BUFFER_ACCESS_TOKEN=your-buffer-token
RAILWAY_URL=https://your-service.up.railway.app
```

### 2.3 Get your keys

**Groq API key**
1. [console.groq.com](https://console.groq.com) → API Keys → Create

**Telegram bot token**
1. Telegram → message @BotFather → `/newbot` → copy token

**GitHub webhook secret**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Buffer access token**
1. [publish.buffer.com/settings/api](https://publish.buffer.com/settings/api) → copy token

### 2.4 Copy Railway URL

After first deploy, Railway gives you a public URL like `https://your-app.up.railway.app`.
Set this as `RAILWAY_URL` in Railway variables.

---

## Phase 3 — GitHub Webhooks

For each repo you want to track:

1. Repo → Settings → Webhooks → Add webhook
2. Fill in:
   - **Payload URL**: `https://your-app.up.railway.app/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: your `GITHUB_WEBHOOK_SECRET`
3. Select individual events:
   - ✅ Pushes
   - ✅ Pull requests
   - ✅ Releases
   - ✅ Issues
   - ✅ Stars
   - ✅ Forks
   - ✅ Repositories
4. Click **Add webhook** — GitHub sends a ping, green checkmark = working

---

## Phase 4 — Dashboard (Vercel)

### 4.1 Deploy

1. Go to [vercel.com](https://vercel.com) → New Project → Import GitHub repo
2. **Root Directory** → set to `dashboard`
3. Framework preset → Next.js (auto-detected)
4. Deploy

### 4.2 Set environment variables

In Vercel → project → Settings → Environment Variables:

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_RAILWAY_URL=https://your-app.up.railway.app
```

---

## Phase 5 — Cron jobs (Railway)

Replace the old GitHub Actions workflows with Railway cron services.

In Railway → New Service → Cron:

| Name | Schedule | Command |
|------|----------|---------|
| Morning focus | `0 7 * * *` | `python -c "import httpx; httpx.post('$RAILWAY_URL/scoring/run')"` |
| Weekly review | `0 20 * * 5` | `python agents/weekly_review.py` |

---

## Verify everything works

### 1. Health check
```
GET https://your-app.up.railway.app/health
→ {"status": "ok"}
```

### 2. Trigger scoring manually
```
POST https://your-app.up.railway.app/scoring/run
→ {"status": "ok", "date": "...", "report": "🎯 FOCUS FOR TODAY..."}
```

### 3. Test Telegram bot
```
/focus      → today's priorities
/status     → project health
/ghost      → activity check
/wins       → recent GitHub events
```

### 4. Test webhook
Make a commit to any tracked repo, then:
```
/wins       → should show the push event
/activity   → should show score > 0
```

### 5. Test content pipeline
Push a release to any tracked repo:
```
/drafts     → should show a pending LinkedIn + X draft
/schedule 1 → approves and queues to Buffer
```

### 6. Run tests
```bash
python -m pytest tests/ -v
→ 75 passed
```

---

## Supabase Row Level Security (optional but recommended)

After verifying everything works, enable RLS on sensitive tables:

```sql
-- Only allow reads from your anon key (dashboard)
alter table content_drafts enable row level security;
create policy "anon read" on content_drafts for select using (true);

-- Block direct inserts/updates from dashboard (Railway handles writes)
create policy "no direct write" on content_drafts for insert with check (false);
```

---

## Environment variable summary

| Variable | Used by | Where to get it |
|----------|---------|----------------|
| `SUPABASE_URL` | Railway, Vercel | Supabase → Settings → API |
| `SUPABASE_KEY` | Railway | Supabase → Settings → API (anon key) |
| `NEXT_PUBLIC_SUPABASE_URL` | Vercel | same as above |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Vercel | same as above |
| `GROQ_API_KEY` | Railway | console.groq.com |
| `TELEGRAM_BOT_TOKEN` | Railway | @BotFather on Telegram |
| `GITHUB_WEBHOOK_SECRET` | Railway | generate with `secrets.token_hex(32)` |
| `BUFFER_ACCESS_TOKEN` | Railway | publish.buffer.com/settings/api |
| `RAILWAY_URL` | Railway, Vercel | Railway dashboard after first deploy |
| `NEXT_PUBLIC_RAILWAY_URL` | Vercel | same as above |
