export interface Activity {
  id: string
  event_type: string
  created_at: string
}

export interface Win {
  id: string
  win_type: string
  created_at: string
}

export interface MomentumResult {
  score: number
  isInactive: boolean
  lastActivityDays: number
  verdict: 'ship' | 'kill' | 'maintain'
}

export function calculateMomentum(
  activities: Activity[],
  wins: Win[],
  lastPush: string | null
): MomentumResult {
  const now = Date.now()
  const lastPushMs = lastPush ? new Date(lastPush).getTime() : 0
  const lastActivityDays = lastPush
    ? Math.round((now - lastPushMs) / (1000 * 60 * 60 * 24))
    : 999

  const decayFactor = lastActivityDays > 7 ? 0.3 : 1.0
  const activityScore = activities.length * 10
  const releaseBonus = wins.filter(w => w.win_type === 'release').length * 50
  const score = Math.min((activityScore + releaseBonus) * decayFactor, 100)
  const isInactive = lastActivityDays > 7

  const verdict =
    score > 60 ? 'ship'
    : score < 20 ? 'kill'
    : 'maintain'

  return { score, isInactive, lastActivityDays, verdict }
}
