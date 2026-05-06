import { NextRequest, NextResponse } from 'next/server'
import { calculateDailyFocus, getTodaysFocus, FocusMode } from '@/lib/focus'

export const revalidate = 300

export async function GET() {
  const data = await getTodaysFocus()
  return NextResponse.json(data ?? { priorities: [], mode: 'normal' })
}

export async function POST(req: NextRequest) {
  const { mode } = await req.json().catch(() => ({}))
  const priorities = await calculateDailyFocus((mode as FocusMode) ?? 'normal')
  return NextResponse.json({ priorities })
}
