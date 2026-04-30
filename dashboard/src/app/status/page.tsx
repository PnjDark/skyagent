import { supabase } from '@/lib/supabase'

export const revalidate = 60

const STATUS_ICON: Record<string, string> = {
  active:       '🟢',
  danger_zone:  '🔴',
  paused:       '⏸',
  ready:        '🚀',
  design:       '✏️',
  maintaining:  '🔧',
  experimental: '🧪',
  archived:     '📦',
  killed:       '💀',
}

const TIER_COLOR: Record<string, string> = {
  S: 'text-yellow-400',
  A: 'text-blue-400',
  B: 'text-green-400',
  C: 'text-zinc-400',
  D: 'text-zinc-600',
}

function daysSince(date: string | null): number | null {
  if (!date) return null
  return Math.floor((Date.now() - new Date(date).getTime()) / 86400000)
}

export default async function StatusPage() {
  const { data: projects } = await supabase
    .from('projects')
    .select('id, tier, status, completion, last_activity, description, next_milestone')
    .order('tier')

  if (!projects?.length) return <div className="text-zinc-500 text-sm">No projects found.</div>

  const groups = projects.reduce<Record<string, typeof projects>>((acc, p) => {
    acc[p.status] = [...(acc[p.status] ?? []), p]
    return acc
  }, {})

  const order = ['active', 'danger_zone', 'ready', 'design', 'maintaining', 'experimental', 'paused', 'archived', 'killed']

  return (
    <div className="space-y-8">
      <h1 className="text-lg font-bold text-white">Project Health</h1>

      {order.filter(s => groups[s]?.length).map(status => (
        <div key={status}>
          <h2 className="text-sm text-zinc-500 mb-3">
            {STATUS_ICON[status]} {status.replace('_', ' ').toUpperCase()} ({groups[status].length})
          </h2>
          <div className="space-y-2">
            {groups[status].map(p => {
              const days = daysSince(p.last_activity)
              const stale = days !== null && days > 14
              return (
                <div key={p.id} className="border border-zinc-800 rounded p-4 flex items-start justify-between gap-4">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold text-sm ${TIER_COLOR[p.tier]}`}>[{p.tier}]</span>
                      <span className="font-bold text-white text-sm">{p.id}</span>
                    </div>
                    <div className="text-xs text-zinc-500">{p.description}</div>
                    {p.next_milestone && (
                      <div className="text-xs text-zinc-400">→ {p.next_milestone}</div>
                    )}
                  </div>
                  <div className="text-right space-y-1 shrink-0">
                    <div className="text-sm font-bold text-white">{p.completion}%</div>
                    <div className={`text-xs ${stale ? 'text-red-400' : 'text-zinc-500'}`}>
                      {days !== null ? `${days}d ago` : 'no activity'}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
