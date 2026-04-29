# 🎯 Focus Engine

AI system that tells you exactly what to work on every morning.

## What it does

- **7 AM daily**: Scores all your projects, generates `outputs/TODAY.md` with 3 priorities
- **Telegram bot**: `/focus`, `/done`, `/status` commands
- **Friday 8 PM**: Weekly review with brutal honesty
- **Auto-tracks**: Logs what you ship, adjusts tomorrow's priorities

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

## Quick start

See [setup/INSTALL.md](setup/INSTALL.md)

## File structure

```
agents/
  focus_engine.py      # Scoring + Gemini report generation
  weekly_review.py     # Friday review
  telegram_bot.py      # /focus /done /status commands
data/
  projects.json        # ⭐ Edit this with your projects
  project_status.json  # Auto-updated by /done
  focus_history.json   # Auto-updated daily
config/
  rules.json           # Scoring weights
outputs/
  TODAY.md             # ⭐ Your daily mission
  WEEKLY_REVIEW.md     # Friday report
```

## Telegram commands

| Command | Action |
|---------|--------|
| `/focus` | Show today's priorities |
| `/generate` | Manually regenerate focus |
| `/done SpecNest Fixed auth bug` | Log progress |
| `/status` | Project health dashboard |
