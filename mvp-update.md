Perfect. Let’s lock the **flow first** so the whole system stays clean and doesn’t turn into a cute chaos machine.

## The core loop

```text
You work
  ↓
GitHub changes happen
  ↓
Agent reads the change
  ↓
Agent updates project memory + momentum
  ↓
Agent updates portfolio feed
  ↓
Agent drafts social posts
  ↓
You approve or edit
  ↓
Buffer schedules posts
  ↓
Tomorrow’s priorities are recalculated
```

---

# The operating model

## 1) GitHub is the source of truth

Your repos create the signal. GitHub webhooks can send your server HTTP POST payloads when repo events happen, and repository webhooks are specifically meant for that kind of event-driven tracking. ([GitHub Docs][1])

## 2) The agent watches only meaningful events

The first version should track:

* new repo created
* repo made public
* push to main
* pull request opened
* pull request merged
* release published
* star / fork growth

That gives you real movement, not noisy micro-commits.

## 3) The agent classifies the event

Each event gets three outputs:

* **importance score**
* **project update**
* **content opportunity**

Example:

```text
release published → very high importance
push to main → medium importance
tiny branch update → low importance
```

## 4) The agent updates your memory

Every meaningful event updates:

* project momentum
* last activity date
* skill signals
* content log
* portfolio feed

## 5) The agent turns it into marketing

Buffer’s API is built around pending/sent updates, profiles, and scheduled times, and Buffer’s publishing flow supports scheduling posts from its dashboard and via integrations. Buffer also supports LinkedIn scheduling and automatic publishing in its docs. ([Buffer][2])

So the flow becomes:

```text
GitHub event
  ↓
Agent writes draft
  ↓
You approve/edit
  ↓
Buffer schedules it
```

That keeps you in control without making you do manual copywriting every time.

---

# The 3-layer system

## Layer A — Data layer

This is the brain’s memory.

Use **Supabase** for:

* `projects`
* `github_events`
* `repo_metrics`
* `content_drafts`
* `scheduled_posts`
* `portfolio_blocks`
* `daily_priorities`

## Layer B — Logic layer

This is your backend on **Railway**.

It handles:

* GitHub webhook intake
* scoring
* content generation
* priority calculation
* Buffer draft creation
* portfolio sync events
* Telegram commands

Railway supports service variables, so your secrets and environment config can live there cleanly. ([Railway Docs][3])

## Layer C — Presentation layer

This is your **Next.js dashboard on Vercel**.

It shows:

* today’s priorities
* GitHub activity
* content queue
* portfolio updates
* scheduled posts
* project status
* brand signals

---

# The two main automated loops

## Morning loop

Every morning:

1. read GitHub activity from the last 24 hours
2. score projects
3. pick 3 priorities
4. generate `TODAY.md`
5. post the morning priorities to Telegram
6. optionally draft a LinkedIn/X post about the focus of the day

## Shipping loop

Whenever you push something meaningful:

1. GitHub webhook fires
2. agent classifies the event
3. portfolio feed updates automatically
4. social draft is generated
5. Buffer queues the post for later
6. project momentum updates

---

# What changes in your portfolio flow

Your portfolio should no longer be a manual CMS you update by hand.

It should read from a live feed like this:

```json
{
  "recent_activity": [
    {
      "project": "SpecNest",
      "event": "release published",
      "summary": "SpecNest beta released",
      "date": "2026-04-30",
      "type": "launch"
    },
    {
      "project": "CIVILPASS",
      "event": "pull request merged",
      "summary": "Contributing guide improved",
      "date": "2026-04-30",
      "type": "community"
    }
  ]
}
```

Then the portfolio automatically:

* shows latest repos
* shows latest shipping activity
* updates descriptions
* updates “recent wins”
* updates the social proof section

---

# What changes in your social flow

A post should be generated from a **real event**, not from a random idea.

Example flow:

```text
GitHub release
  ↓
Agent drafts LinkedIn post
  ↓
Agent drafts short X post
  ↓
Agent suggests description update for portfolio card
  ↓
You approve
  ↓
Buffer schedules it
```

And the post legend/description should be tied to the repo event, so when the repo changes, the post metadata can be refreshed too.

---

# Telegram commands in this version

Keep Telegram simple and useful:

* `/focus` → today’s priorities
* `/done` → manually log a win
* `/wins` → recent GitHub-backed wins
* `/activity` → repo activity summary
* `/ghost` → “you’ve been quiet” check
* `/drafts` → content drafts waiting for approval
* `/schedule` → send approved draft to Buffer
* `/status` → project health snapshot

---

# What the first build should look like

## Phase 1 — Foundation

* Supabase database
* Railway backend
* GitHub webhook listener
* Telegram bot
* basic scoring engine

## Phase 2 — Intelligence

* project discovery from GitHub
* repo classification
* momentum scoring
* daily priorities generation

## Phase 3 — Marketing

* content draft generator
* approval queue
* Buffer scheduling
* post history

## Phase 4 — Portfolio

* Next.js dashboard
* live activity feed
* auto-updating project cards
* recent shipping section

---

# The key design decision

You asked for **assistant + social media marketer**.

So the system should stay in **semi-automated mode**:

* automatic detection
* automatic drafting
* automatic scoring
* automatic portfolio updates
* **manual approval before publishing**

That keeps your voice sharp and protects your brand.

---

# The cleanest mental model

```text
GitHub = what you built
Focus Agent = what matters
Portfolio = what the world sees
Buffer = when the world sees it
Telegram = your control panel
Supabase = memory
Railway = backend engine
Vercel = public face
```

That is the flow I’d build for you.

If you want, next I’ll turn this into the **exact database schema + backend endpoints + dashboard pages** so we can build it layer by layer.

[1]: https://docs.github.com/en/rest/repos/webhooks?utm_source=chatgpt.com "REST API endpoints for repository webhooks"
[2]: https://buffer.com/developers/api?utm_source=chatgpt.com "Buffer API - Developers"
[3]: https://docs.railway.com/variables?utm_source=chatgpt.com "Using Variables | Railway Docs"
