import { query, queryOne } from './db'
import { calculateMomentum } from './momentum'

export type FocusMode = 'normal' | 'low-energy' | 'beast'

export interface FocusPriority {
  projectId: string
  repo: string
  score: number
  verdict: string
  reason: string
}

export async function calculateDailyFocus(mode: FocusMode = 'normal'): Promise<FocusPriority[]> {
  const projects = await query<{
    id: string
    repo_name: string
    last_push: string | null
  }>(`SELECT id, repo_name, last_push FROM projects ORDER BY momentum_score DESC LIMIT 20`)

  const scored = await Promise.all(
    projects.map(async p => {
      const activities = await query<{ id: string; event_type: string; created_at: string }>(
        `SELECT id, event_type, created_at FROM activities
         WHERE project_id = $1 AND created_at > NOW() - INTERVAL '7 days'`,
        [p.id]
      )
      const wins = await query<{ id: string; win_type: string; created_at: string }>(
        `SELECT id, win_type, created_at FROM wins
         WHERE project_id = $1 AND created_at > NOW() - INTERVAL '30 days'`,
        [p.id]
      )
      const { score, isInactive, verdict } = calculateMomentum(activities, wins, p.last_push)
      return { projectId: p.id, repo: p.repo_name, score, isInactive, verdict }
    })
  )

  let ranked = scored.sort((a, b) => b.score - a.score)

  if (mode === 'low-energy') ranked = ranked.filter(p => !p.isInactive)
  // beast + normal: take top as-is

  const top = ranked.slice(0, 3).map(p => ({
    projectId: p.projectId,
    repo: p.repo,
    score: Math.round(p.score),
    verdict: p.verdict,
    reason:
      p.score > 70 ? 'High momentum — push for release'
      : p.score > 40 ? 'Active — capitalize on recent work'
      : p.isInactive ? 'Stale — needs a push or cut'
      : 'Low momentum — maintain or kill',
  }))

  await query(
    `INSERT INTO daily_focus (date, priorities, mode)
     VALUES (CURRENT_DATE, $1, $2)
     ON CONFLICT (date) DO UPDATE SET priorities = $1, mode = $2`,
    [JSON.stringify(top), mode]
  )

  return top
}

export async function getTodaysFocus(): Promise<{ priorities: FocusPriority[]; mode: string } | null> {
  return queryOne<{ priorities: FocusPriority[]; mode: string }>(
    `SELECT priorities, mode FROM daily_focus WHERE date = CURRENT_DATE`
  )
}
