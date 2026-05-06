'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

const RAILWAY_URL = process.env.NEXT_PUBLIC_RAILWAY_URL!

type Draft = {
  id: number
  project_id: string
  linkedin_draft: string
  x_draft: string
  portfolio_update: string
  status: string
  created_at: string
}

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState<number | null>(null)
  const [message, setMessage] = useState<{ id: number; text: string; ok: boolean } | null>(null)

  useEffect(() => {
    supabase
      .from('content_drafts')
      .select('id, project_id, linkedin_draft, x_draft, portfolio_update, status, created_at')
      .eq('status', 'pending')
      .order('created_at', { ascending: false })
      .then(({ data }) => {
        setDrafts(data ?? [])
        setLoading(false)
      })
  }, [])

  async function approve(id: number) {
    setActing(id)
    const r = await fetch(`${RAILWAY_URL}/content/drafts/${id}/approve`, { method: 'POST' })
    const ok = r.ok
    setMessage({ id, text: ok ? '✅ Queued on Buffer' : '❌ Failed — check Railway logs', ok })
    if (ok) setDrafts(d => d.filter(x => x.id !== id))
    setActing(null)
  }

  async function reject(id: number) {
    setActing(id)
    await fetch(`${RAILWAY_URL}/content/drafts/${id}/reject`, { method: 'POST' })
    setDrafts(d => d.filter(x => x.id !== id))
    setActing(null)
  }

  if (loading) return <div className="text-zinc-500 text-sm">Loading drafts...</div>
  if (!drafts.length) return <div className="text-zinc-500 text-sm">No pending drafts. Keep shipping.</div>

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-bold text-white">Content Drafts</h1>

      {drafts.map(d => (
        <div key={d.id} className="border border-zinc-800 rounded p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-bold text-white text-sm">{d.project_id}</span>
              <span className="text-xs text-zinc-500 ml-3">{new Date(d.created_at).toLocaleDateString()}</span>
            </div>
            <span className="text-xs text-zinc-600">#{d.id}</span>
          </div>

          <div className="space-y-3">
            <div>
              <div className="text-xs text-zinc-500 mb-1">LinkedIn</div>
              <p className="text-sm text-zinc-300 leading-relaxed">{d.linkedin_draft}</p>
            </div>
            <div>
              <div className="text-xs text-zinc-500 mb-1">X</div>
              <p className="text-sm text-zinc-300">{d.x_draft}</p>
            </div>
            {d.portfolio_update && (
              <div>
                <div className="text-xs text-zinc-500 mb-1">Portfolio update</div>
                <p className="text-sm text-zinc-400 italic">{d.portfolio_update}</p>
              </div>
            )}
          </div>

          {message?.id === d.id && (
            <div className={`text-xs ${message.ok ? 'text-green-400' : 'text-red-400'}`}>
              {message.text}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => approve(d.id)}
              disabled={acting === d.id}
              className="px-4 py-1.5 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-xs rounded transition-colors"
            >
              {acting === d.id ? 'Sending...' : 'Approve & Queue'}
            </button>
            <button
              onClick={() => reject(d.id)}
              disabled={acting === d.id}
              className="px-4 py-1.5 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-zinc-300 text-xs rounded transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
