import { query } from '@/lib/db'
import { getTodaysFocus } from '@/lib/focus'

export const dynamic = 'force-dynamic'

async function getData() {
  const [projects, wins, activity, focus] = await Promise.all([
    query<{ id: string; repo_name: string; description: string; momentum_score: number; github_url: string }>(
      `SELECT id, repo_name, description, momentum_score, github_url
       FROM projects ORDER BY momentum_score DESC LIMIT 10`
    ),
    query<{ id: string; title: string; win_type: string; repo_name: string; created_at: string }>(
      `SELECT w.id, w.title, w.win_type, w.created_at, p.repo_name
       FROM wins w JOIN projects p ON w.project_id = p.id
       ORDER BY w.created_at DESC LIMIT 5`
    ),
    query<{ id: string; event_type: string; repo_name: string; created_at: string }>(
      `SELECT a.id, a.event_type, a.created_at, p.repo_name
       FROM activities a JOIN projects p ON a.project_id = p.id
       ORDER BY a.created_at DESC LIMIT 10`
    ),
    getTodaysFocus(),
  ])
  return { projects, wins, activity, focus }
}

export default async function Home() {
  const { projects, wins, activity, focus } = await getData()

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-mono p-8">
      <div className="max-w-4xl mx-auto space-y-12">

        <h1 className="text-2xl font-bold text-white">⚡ Sky Agent</h1>

        {/* Today's Focus */}
        <section>
          <h2 className="text-sm text-zinc-500 uppercase tracking-widest mb-4">🎯 Today's Focus</h2>
          {focus?.priorities?.length ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {focus.priorities.map((p, i) => (
                <div key={p.projectId} className="border border-zinc-800 rounded p-4 space-y-1">
                  <div className="text-xs text-zinc-500">#{i + 1}</div>
                  <div className="font-bold text-white">{p.repo}</div>
                  <div className="text-xs text-zinc-400">{p.score}pts · {p.verdict}</div>
                  <div className="text-xs text-zinc-500">{p.reason}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-zinc-600 text-sm">No focus yet. POST /api/focus or run /focus in Telegram.</p>
          )}
        </section>

        {/* Recent Wins */}
        <section>
          <h2 className="text-sm text-zinc-500 uppercase tracking-widest mb-4">🏆 Recent Wins</h2>
          {wins.length ? (
            <div className="space-y-2">
              {wins.map(w => (
                <div key={w.id} className="flex items-center justify-between border border-zinc-800 rounded px-4 py-3">
                  <div>
                    <span className="text-white text-sm font-medium">{w.title}</span>
                    <span className="text-zinc-500 text-xs ml-2">{w.repo_name}</span>
                  </div>
                  <span className="text-xs text-zinc-600">{new Date(w.created_at).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-zinc-600 text-sm">No wins yet. Merge a PR or cut a release.</p>
          )}
        </section>

        {/* Projects */}
        <section>
          <h2 className="text-sm text-zinc-500 uppercase tracking-widest mb-4">🚀 Projects</h2>
          {projects.length ? (
            <div className="space-y-2">
              {projects.map(p => (
                <a
                  key={p.id}
                  href={p.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between border border-zinc-800 rounded px-4 py-3 hover:border-zinc-600 transition-colors"
                >
                  <div>
                    <span className="text-white text-sm font-medium">{p.repo_name}</span>
                    {p.description && (
                      <span className="text-zinc-500 text-xs ml-2">{p.description}</span>
                    )}
                  </div>
                  <span className="text-sm font-bold text-zinc-300">{Math.round(p.momentum_score)}</span>
                </a>
              ))}
            </div>
          ) : (
            <p className="text-zinc-600 text-sm">No projects yet. Push to a repo with the GitHub webhook configured.</p>
          )}
        </section>

        {/* Activity Feed */}
        <section>
          <h2 className="text-sm text-zinc-500 uppercase tracking-widest mb-4">📈 Activity</h2>
          {activity.length ? (
            <div className="space-y-1">
              {activity.map(a => (
                <div key={a.id} className="flex items-center gap-3 text-xs text-zinc-400">
                  <span className="text-zinc-600">{new Date(a.created_at).toLocaleString()}</span>
                  <span className="text-zinc-300">{a.repo_name}</span>
                  <span className="bg-zinc-800 px-1.5 py-0.5 rounded">{a.event_type}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-zinc-600 text-sm">No activity yet.</p>
          )}
        </section>

      </div>
    </div>
  )
}
