import { supabase } from '@/lib/supabase'

export const revalidate = 300 // refresh every 5 min

async function getToday() {
  const today = new Date().toISOString().split('T')[0]
  const { data } = await supabase
    .from('daily_priorities')
    .select('content, priorities, generated_at')
    .eq('date', today)
    .single()
  return data
}

export default async function TodayPage() {
  const data = await getToday()

  if (!data) {
    return (
      <div className="text-zinc-500 text-sm">
        No focus generated yet today. Trigger <code className="text-zinc-300">/scoring/run</code> or use <code className="text-zinc-300">/generate</code> in Telegram.
      </div>
    )
  }

  const priorities: { name: string; score: number; tier: string }[] = data.priorities ?? []
  const generatedAt = new Date(data.generated_at).toLocaleTimeString()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-white">Today&apos;s Focus</h1>
        <span className="text-xs text-zinc-500">Generated {generatedAt}</span>
      </div>

      {priorities.length > 0 && (
        <div className="flex gap-3">
          {priorities.map((p, i) => (
            <div key={p.name} className="flex-1 border border-zinc-800 rounded p-3 space-y-1">
              <div className="text-xs text-zinc-500">#{i + 1}</div>
              <div className="font-bold text-white text-sm">{p.name}</div>
              <div className="flex items-center gap-2">
                <span className="text-xs bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-300">{p.tier}</span>
                <span className="text-xs text-zinc-400">{p.score}pts</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <pre className="whitespace-pre-wrap text-sm text-zinc-300 leading-relaxed border border-zinc-800 rounded p-4">
        {data.content}
      </pre>
    </div>
  )
}
