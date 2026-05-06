import { supabase } from '@/lib/supabase'

export const revalidate = 120

const TYPE_STYLE: Record<string, string> = {
  launch:    'bg-green-900 text-green-300',
  update:    'bg-blue-900 text-blue-300',
  community: 'bg-purple-900 text-purple-300',
  milestone: 'bg-yellow-900 text-yellow-300',
}

export default async function PortfolioPage() {
  const { data: feed } = await supabase
    .from('portfolio_feed')
    .select('id, project_id, event_type, summary, date, type')
    .order('date', { ascending: false })
    .limit(30)

  const { data: projects } = await supabase
    .from('projects')
    .select('id, tier, description, completion, status, github_repo')
    .not('status', 'in', '(archived,killed)')
    .order('tier')

  return (
    <div className="space-y-10">
      <h1 className="text-lg font-bold text-white">Portfolio</h1>

      {/* Project cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {projects?.map(p => (
          <div key={p.id} className="border border-zinc-800 rounded p-4 space-y-2">
            <div className="flex items-start justify-between">
              <span className="font-bold text-white text-sm">{p.id}</span>
              <span className="text-xs text-zinc-500">{p.tier}</span>
            </div>
            <p className="text-xs text-zinc-400">{p.description}</p>
            <div className="flex items-center gap-3">
              {/* Completion bar */}
              <div className="flex-1 h-1 bg-zinc-800 rounded overflow-hidden">
                <div className="h-full bg-blue-500 rounded" style={{ width: `${p.completion}%` }} />
              </div>
              <span className="text-xs text-zinc-500 shrink-0">{p.completion}%</span>
            </div>
            {p.github_repo && (
              <a
                href={`https://github.com/${p.github_repo}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-zinc-600 hover:text-zinc-400 transition-colors"
              >
                github.com/{p.github_repo}
              </a>
            )}
          </div>
        ))}
      </div>

      {/* Live activity feed */}
      <div>
        <h2 className="text-sm text-zinc-500 mb-4">Recent Shipping Activity</h2>
        {!feed?.length ? (
          <div className="text-zinc-600 text-sm">No activity yet.</div>
        ) : (
          <div className="space-y-2">
            {feed.map(item => (
              <div key={item.id} className="flex items-start gap-4 text-sm">
                <span className="text-zinc-600 shrink-0 w-24 text-xs pt-0.5">{item.date}</span>
                <span className="font-medium text-zinc-300 shrink-0 w-28 text-xs pt-0.5">{item.project_id}</span>
                <span className="text-zinc-400 flex-1 text-xs">{item.summary}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded shrink-0 ${TYPE_STYLE[item.type] ?? 'bg-zinc-800 text-zinc-400'}`}>
                  {item.type}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
