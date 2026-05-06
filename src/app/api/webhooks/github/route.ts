import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'
import { query, queryOne } from '@/lib/db'

function verifySignature(body: string, signature: string | null): boolean {
  if (!signature) return false
  const hash = `sha256=${crypto
    .createHmac('sha256', process.env.GITHUB_WEBHOOK_SECRET!)
    .update(body)
    .digest('hex')}`
  return crypto.timingSafeEqual(Buffer.from(hash), Buffer.from(signature))
}

async function upsertProject(repo: {
  name: string
  html_url: string
  description: string | null
}): Promise<string> {
  const existing = await queryOne<{ id: string }>(
    `SELECT id FROM projects WHERE repo_name = $1`,
    [repo.name]
  )
  if (existing) return existing.id

  const created = await queryOne<{ id: string }>(
    `INSERT INTO projects (repo_name, github_url, description, last_push)
     VALUES ($1, $2, $3, NOW()) RETURNING id`,
    [repo.name, repo.html_url, repo.description ?? '']
  )
  return created!.id
}

export async function POST(req: NextRequest) {
  const body = await req.text()
  const signature = req.headers.get('x-hub-signature-256')

  if (!verifySignature(body, signature)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const event = req.headers.get('x-github-event') ?? ''
  const payload = JSON.parse(body)
  const { repository, action, pull_request, release } = payload

  try {
    const projectId = await upsertProject(repository)

    // Log activity
    await query(
      `INSERT INTO activities (project_id, event_type, event_data)
       VALUES ($1, $2, $3)`,
      [projectId, event, payload]
    )

    // Log wins for releases and merged PRs
    if (event === 'release') {
      await query(
        `INSERT INTO wins (project_id, title, win_type) VALUES ($1, $2, 'release')`,
        [projectId, release?.name ?? release?.tag_name ?? 'Release']
      )
    } else if (event === 'pull_request' && action === 'closed' && pull_request?.merged) {
      await query(
        `INSERT INTO wins (project_id, title, win_type) VALUES ($1, $2, 'merge')`,
        [projectId, pull_request.title]
      )
    }

    // Recalculate momentum score
    const [{ count }] = await query<{ count: string }>(
      `SELECT COUNT(*) as count FROM activities
       WHERE project_id = $1 AND created_at > NOW() - INTERVAL '7 days'`,
      [projectId]
    )
    const momentum = Math.min(parseInt(count) * 15, 100)

    await query(
      `UPDATE projects SET momentum_score = $1, last_push = NOW() WHERE id = $2`,
      [momentum, projectId]
    )

    return NextResponse.json({ ok: true, projectId, event })
  } catch (err) {
    console.error('GitHub webhook error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
