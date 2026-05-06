import { NextResponse } from 'next/server'
import { query } from '@/lib/db'

export const revalidate = 60

export async function GET() {
  const rows = await query(
    `SELECT w.id, w.title, w.win_type, w.created_at, p.repo_name
     FROM wins w JOIN projects p ON w.project_id = p.id
     ORDER BY w.created_at DESC LIMIT 20`
  )
  return NextResponse.json(rows)
}
