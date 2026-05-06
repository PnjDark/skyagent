import { NextResponse } from 'next/server'
import { query } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET() {
  const rows = await query(
    `SELECT id, repo_name, github_url, description, momentum_score, last_push, created_at
     FROM projects ORDER BY momentum_score DESC`
  )
  return NextResponse.json(rows)
}
