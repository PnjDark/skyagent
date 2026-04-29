# 🎯 Focus Engine

AI system that tells you exactly what to work on every morning — now with GitHub intelligence.

## What it does

- **7 AM daily**: Scores all your projects, generates `outputs/TODAY.md` with 3 priorities (powered by Groq/Llama)
- **Telegram bot**: `/focus`, `/done`, `/status`, `/wins`, `/ghost`, `/activity` commands
- **Friday 8 PM**: Weekly review with brutal honesty
- **Auto-tracks**: Logs what you ship, adjusts tomorrow's priorities
- **GitHub webhooks**: Every push, PR, release, and star feeds directly into your priority scores

## How priorities are scored

| Factor | Points |
|--------|--------|
| Tier (S/A/B/C) | 5–30 |
| Deadline urgency | 0–20 |
| Revenue potential | 0–15 |
| Recent momentum | 0–15 |
| Stuck 21+ days | −20 |
| 70–90% complete | +10 |
| Manual boost | variable |
| GitHub activity (last 7 days) | 0–20 |

## Quick start

See [setup/INSTALL.md](setup/INSTALL.md)

## File structure

```
agents/
  focus_engine.py          # Scoring + Groq/Llama report generation
  github_intelligence.py   # Webhook event processing + momentum scoring
  github_scoring.py        # GitHub boost calculation for priority scores
  weekly_review.py         # Friday review
  telegram_bot.py          # All bot commands
api/
  main.py                  # FastAPI webhook server
data/
  projects.json            # ⭐ Edit this with your projects
  project_status.json      # Auto-updated by /done
  focus_history.json       # Auto-updated daily
  github_cache.json        # Auto-updated by webhooks
config/
  rules.json               # Scoring weights
outputs/
  TODAY.md                 # ⭐ Your daily mission
  WEEKLY_REVIEW.md         # Friday report
  activity.json            # Recent GitHub activity feed
```

## Adding a project

In `data/projects.json`, include a `github_repo` field to enable GitHub scoring:

```json
"SpecNest": {
  "tier": "A",
  "status": "active",
  "github_repo": "penjy/specnest"
}
```

## Telegram commands

| Command | Action |
|---------|--------|
| `/focus` | Show today's priorities |
| `/generate` | Manually regenerate focus |
| `/done SpecNest Fixed auth bug` | Log progress |
| `/status` | Project health dashboard |
| `/wins` | Recent GitHub activity (last 10 events) |
| `/ghost` | Check if you've gone quiet (< 50 pts in 5 days) |
| `/activity` | Weekly GitHub score summary by repo |

## GitHub event scoring

| Event | Points |
|-------|--------|
| Push to main/master | 30 + 5 per commit |
| Push to other branch | 10 + 2 per commit |
| Release published | 90 |
| PR merged | 70 |
| PR opened | 20 |
| Issue closed | 15 |
| Fork | 10 |
| Star | 5 |

A repo with 200+ points in a week gets the full +20 boost to its project priority score.
