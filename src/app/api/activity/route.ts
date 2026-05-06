import { NextResponse } from 'next/server'
import { query } from '@/lib/db'

export const revalidate = 30

export async function GET() {
  const rows = await query(
    `SELECT a.id, a.event_type, a.created_at, p.repo_name
     FROM activities a JOIN projects p ON a.project_id = p.id
     ORDER BY a.created_at DESC LIMIT 50`
  )
  return NextResponse.json(rows)
}
