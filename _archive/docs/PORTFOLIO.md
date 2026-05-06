# Live Portfolio Integration

Focus Engine is the backend source for your real personal portfolio.

Your public Next.js portfolio should fetch this API:

```text
GET https://your-railway-service.up.railway.app/portfolio/feed
```

It returns portfolio-ready JSON:

```json
{
  "generated_at": "2026-05-01T06:30:00+00:00",
  "projects": [
    {
      "id": "SpecNest",
      "title": "SpecNest",
      "tier": "A",
      "status": "active",
      "category": "marketplace",
      "description": "Computer marketplace for Cameroon",
      "next_milestone": "Launch beta",
      "completion": 75,
      "github_repo": "PnjDark/specnest",
      "github_url": "https://github.com/PnjDark/specnest",
      "last_activity": "2026-05-01"
    }
  ],
  "recent_activity": [
    {
      "id": 1,
      "project_id": "SpecNest",
      "event_type": "release",
      "summary": "Released v1.0",
      "date": "2026-05-01",
      "type": "launch"
    }
  ]
}
```

## Environment Variable

In your real portfolio project, add:

```bash
FOCUS_ENGINE_API_URL=https://your-railway-service.up.railway.app
```

Do not expose Supabase keys in your portfolio. Your portfolio should only call Focus Engine's public portfolio endpoint.

## Next.js Fetch Helper

Create this in your portfolio app:

```ts
// src/lib/focus-engine.ts
export type FocusProject = {
  id: string
  title: string
  tier: string | null
  status: string | null
  category: string | null
  description: string | null
  next_milestone: string | null
  completion: number
  github_repo: string | null
  github_url: string | null
  last_activity: string | null
}

export type FocusActivity = {
  id: number
  project_id: string
  event_type: string | null
  summary: string | null
  date: string | null
  type: string
}

export type FocusPortfolioFeed = {
  generated_at: string
  projects: FocusProject[]
  recent_activity: FocusActivity[]
}

export async function getFocusPortfolioFeed(): Promise<FocusPortfolioFeed> {
  const baseUrl = process.env.FOCUS_ENGINE_API_URL

  if (!baseUrl) {
    throw new Error('FOCUS_ENGINE_API_URL is not set')
  }

  const res = await fetch(`${baseUrl.replace(/\/$/, '')}/portfolio/feed`, {
    next: { revalidate: 300 },
  })

  if (!res.ok) {
    throw new Error(`Focus Engine portfolio API failed: ${res.status}`)
  }

  return res.json()
}
```

## Example Projects Section

```tsx
// src/app/projects/page.tsx
import { getFocusPortfolioFeed } from '@/lib/focus-engine'

export default async function ProjectsPage() {
  const feed = await getFocusPortfolioFeed()

  return (
    <main className="space-y-10">
      <section className="grid gap-4 md:grid-cols-2">
        {feed.projects.map(project => (
          <article key={project.id} className="rounded border p-4">
            <div className="flex items-start justify-between gap-4">
              <h2 className="font-semibold">{project.title}</h2>
              {project.tier && <span className="text-sm">{project.tier}</span>}
            </div>

            {project.description && (
              <p className="mt-2 text-sm text-zinc-600">{project.description}</p>
            )}

            <div className="mt-4 h-1.5 rounded bg-zinc-200">
              <div
                className="h-full rounded bg-zinc-900"
                style={{ width: `${project.completion}%` }}
              />
            </div>

            {project.github_url && (
              <a className="mt-3 block text-sm underline" href={project.github_url}>
                GitHub
              </a>
            )}
          </article>
        ))}
      </section>

      <section>
        <h2 className="font-semibold">Recent Shipping</h2>
        <div className="mt-4 space-y-3">
          {feed.recent_activity.map(item => (
            <div key={item.id} className="text-sm">
              <span className="font-medium">{item.project_id}</span>
              {item.summary && <span> - {item.summary}</span>}
              {item.date && <span className="text-zinc-500"> ({item.date})</span>}
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}
```

## Flow

```text
GitHub event
  -> Focus Engine Railway API
  -> Supabase portfolio_feed/projects
  -> /portfolio/feed
  -> Your real Next.js portfolio
```

## Deploy Checklist

- Railway backend is live.
- `RAILWAY_URL` is set correctly for bot/internal calls.
- Supabase contains project rows with `github_repo` values.
- GitHub webhooks are sending events to `/webhooks/github`.
- Your real portfolio has `FOCUS_ENGINE_API_URL` set.
- Your portfolio page fetches `/portfolio/feed` with ISR/revalidation.
