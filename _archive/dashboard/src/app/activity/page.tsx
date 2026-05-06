import { supabase } from '@/lib/supabase'

export const revalidate = 60

const EVENT_ICON: Record<string, string> = {
  push_main:       '⬆️',
  push_branch:     '🌿',
  release:         '🚀',
  pr_merged:       '✅',
  pr_opened:       '🔀',
  issue_closed:    '✔️',
  fork:            '🍴',
  star:            '⭐',
  repo_created:    '🆕',
  repo_publicized: '📢',
}

export default async function ActivityPage() {
  const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString()

  const { data: events } = await supabase
    .from('github_events')
    .select('repo, event_type, points, importance, processed_at')
    .gte('processed_at', weekAgo)
    .order('processed_at', { ascending: false })

  if (!events?.length) {
    return <div className="text-zinc-500 text-sm">No GitHub activity in the last 7 days.</div>
  }

  // Group by repo
  const byRepo = events.reduce<Record<string, { total: number; events: typeof events }>>((acc, e) => {
    if (!acc[e.repo]) acc[e.repo] = { total: 0, events: [] }
    acc[e.repo].total += e.points
    acc[e.repo].events.push(e)
    return acc
  }, {})

  const sorted = Object.entries(byRepo).sort((a, b) => b[1].total - a[1].total)

  return (
    <div className="space-y-8">
      <h1 className="text-lg font-bold text-white">GitHub Activity — Last 7 Days</h1>

      {sorted.map(([repo, { total, events: repoEvents }]) => {
        const boost = Math.min(20, Math.floor(total * 20 / 200))
        return (
          <div key={repo} className="border border-zinc-800 rounded p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white text-sm">{repo}</span>
              <div className="flex items-center gap-3 text-xs">
                <span className="text-zinc-400">{total}pts</span>
                <span className={`px-2 py-0.5 rounded ${boost >= 20 ? 'bg-green-900 text-green-300' : boost > 0 ? 'bg-zinc-800 text-zinc-300' : 'text-zinc-600'}`}>
                  +{boost} boost
                </span>
              </div>
            </div>

            {/* Points bar */}
            <div className="h-1.5 bg-zinc-800 rounded overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded"
                style={{ width: `${Math.min(100, total / 2)}%` }}
              />
            </div>

            <div className="space-y-1">
              {repoEvents.slice(0, 8).map((e, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-zinc-400">
                    {EVENT_ICON[e.event_type] ?? '•'} {e.event_type.replace('_', ' ')}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className={`${e.importance === 'high' ? 'text-green-400' : e.importance === 'medium' ? 'text-yellow-400' : 'text-zinc-600'}`}>
                      +{e.points}pts
                    </span>
                    <span className="text-zinc-600">{new Date(e.processed_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
