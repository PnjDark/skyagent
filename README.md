# 🎯 Focus Engine

AI system that tells you exactly what to work on, turns your GitHub activity into social content, and keeps your portfolio live — automatically.

## What it does

- **7 AM daily**: Scores all projects, picks 3 priorities, sends them to Telegram
- **GitHub webhooks**: Every push, PR, release, and star feeds into priority scores and triggers content drafts
- **Content pipeline**: High-impact events (releases, merged PRs) auto-generate LinkedIn + X posts via Groq — you approve before anything goes live
- **Buffer scheduling**: Approved drafts queue directly to Buffer via GraphQL API
- **Live portfolio feed**: Every meaningful ship updates your portfolio automatically
- **Dashboard**: Next.js app on Vercel shows today's focus, project health, GitHub activity, draft queue, and portfolio
- **Telegram bot**: Full control panel — focus, logging, drafts, scheduling, ghost check
- **Friday 8 PM**: Weekly review with brutal honesty

## System architecture

```
GitHub
  │ webhook POST
  ▼
Railway (FastAPI)
  ├── scores event → Supabase: github_events
  ├── updates project last_activity
  └── if high importance → Groq drafts → Supabase: content_drafts
          │
          ▼
Telegram bot / Vercel dashboard
  └── you approve draft
          │
          ▼
      Buffer API → LinkedIn + X

Railway cron (7 AM)
  └── reads projects + github_events → Groq → Supabase: daily_priorities → Telegram
```

## How priorities are scored

| Factor | Points |
|--------|--------|
| Tier (S/A/B/C/D) | 5–30 |
| Deadline urgency | 0–20 |
| Revenue potential | 0–15 |
| Recent momentum | 0–15 |
| Stuck 14+ days | −20 |
| 70–90% complete | +10 |
| Manual boost | variable |
| GitHub activity (last 7 days) | 0–20 |

## GitHub event scoring

| Event | Points |
|-------|--------|
| Push to main/master | 30 + 5 per commit |
| Push to other branch | 10 + 2 per commit |
| Release published | 90 |
| PR merged | 70 |
| PR opened | 20 |
| Issue closed | 15 |
| Repo publicized | 40 |
| Repo created | 25 |
| Fork | 10 |
| Star | 5 |

A repo with 200+ points in a week gets the full +20 boost to its project priority score.

## Content draft triggers

These events auto-generate LinkedIn + X drafts via Groq:

| Event | Draft type |
|-------|-----------|
| Release published | Launch post |
| PR merged | Shipping update |
| Repo publicized | Announcement |
| Repo created | New project intro |

## Telegram commands

| Command | Action |
|---------|--------|
| `/focus` | Today's priorities |
| `/generate` | Manually regenerate focus |
| `/done SpecNest Fixed auth bug` | Log progress |
| `/status` | Project health dashboard |
| `/wins` | Recent high-impact GitHub events |
| `/activity` | 7-day GitHub score by repo |
| `/ghost` | Alert if < 50pts in 5 days |
| `/drafts` | Pending content drafts |
| `/schedule <id>` | Approve draft and queue to Buffer |

## Dashboard pages (Vercel)

| Page | What it shows |
|------|--------------|
| `/` | Today's focus report + top 3 priorities |
| `/status` | All projects grouped by status with completion |
| `/activity` | GitHub events last 7 days with boost preview |
| `/drafts` | Approve / reject content drafts |
| `/portfolio` | Project cards + live shipping activity feed |

## File structure

```
agents/
  db.py                    # Supabase client singleton
  focus_engine.py          # Legacy local scoring (superseded by api/scoring.py)
  weekly_review.py         # Friday review — reads from Supabase
  telegram_bot.py          # All bot commands — reads/writes Supabase
api/
  main.py                  # FastAPI app — mounts all routers
  webhooks.py              # GitHub webhook intake + event scoring
  scoring.py               # Priority scoring + Groq report generation
  content.py               # Draft generation + approve/reject endpoints
  buffer.py                # Buffer GraphQL API — schedule/save as draft
dashboard/
  src/app/                 # Next.js App Router pages
  src/lib/supabase.ts      # Supabase client for dashboard
setup/
  schema.sql               # ⭐ Run this first in Supabase SQL editor
  migrate.py               # One-time migration from JSON files to Supabase
  migrate_phase4.sql       # Add buffer_post_ids column (if schema already applied)
  INSTALL.md               # Full deployment guide
tests/
  conftest.py              # Shared fixtures + dependency stubs
  test_webhooks.py         # 22 tests — event scoring, HMAC, endpoint
  test_scoring.py          # 20 tests — score logic, priorities, DB writes
  test_content.py          # 8 tests  — draft generation, approve/reject
  test_buffer.py           # 12 tests — GraphQL, channels, schedule flows
config/
  rules.json               # Scoring weights reference
```

## Adding a project

Add to the `projects` table in Supabase. Include `github_repo` to enable GitHub scoring:

```json
{
  "id": "SpecNest",
  "tier": "A",
  "status": "active",
  "github_repo": "penjy/specnest",
  "revenue_potential": "direct",
  "completion": 75,
  "description": "Computer marketplace for Cameroon",
  "next_milestone": "Fix auth bug, launch beta"
}
```

## Quick start

See [setup/INSTALL.md](setup/INSTALL.md)
