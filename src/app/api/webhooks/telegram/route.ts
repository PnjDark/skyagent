import { NextRequest, NextResponse } from 'next/server'
import { query } from '@/lib/db'
import { calculateDailyFocus, getTodaysFocus } from '@/lib/focus'

const TELEGRAM_API = `https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}`

async function send(chatId: number, text: string) {
  await fetch(`${TELEGRAM_API}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'HTML' }),
  })
}

async function handleCommand(chatId: number, text: string) {
  const [command, ...args] = text.trim().split(' ')

  switch (command) {
    case '/focus': {
      const mode = (args[0] as 'normal' | 'low-energy' | 'beast') ?? 'normal'
      const priorities = await calculateDailyFocus(mode)
      const lines = priorities.map(
        (p, i) => `<b>${i + 1}. ${p.repo}</b>\n📊 ${p.score}pts · ${p.verdict}\n💡 ${p.reason}`
      )
      await send(chatId, `🎯 <b>Today's Focus</b> [${mode}]\n\n${lines.join('\n\n')}`)
      break
    }

    case '/today': {
      const data = await getTodaysFocus()
      if (!data) {
        await send(chatId, 'No focus yet today. Run /focus to generate.')
        break
      }
      const lines = data.priorities.map(
        (p, i) => `<b>${i + 1}. ${p.repo}</b> — ${p.reason}`
      )
      await send(chatId, `🎯 <b>Today's Focus</b>\n\n${lines.join('\n')}`)
      break
    }

    case '/wins': {
      const wins = await query<{ title: string; repo_name: string; created_at: string }>(
        `SELECT w.title, p.repo_name, w.created_at
         FROM wins w JOIN projects p ON w.project_id = p.id
         ORDER BY w.created_at DESC LIMIT 5`
      )
      if (!wins.length) { await send(chatId, 'No wins yet.'); break }
      const lines = wins.map(w => `✅ <b>${w.title}</b> (${w.repo_name})`)
      await send(chatId, `🏆 <b>Recent Wins</b>\n\n${lines.join('\n')}`)
      break
    }

    case '/ghost': {
      const stale = await query<{ repo_name: string; momentum_score: number }>(
        `SELECT repo_name, momentum_score FROM projects
         WHERE last_push < NOW() - INTERVAL '7 days'
         ORDER BY momentum_score DESC`
      )
      if (!stale.length) { await send(chatId, '✅ All projects active!'); break }
      const lines = stale.map(p => `👻 <b>${p.repo_name}</b> (${Math.round(p.momentum_score)}pts)`)
      await send(chatId, `<b>Inactive Projects</b>\n\n${lines.join('\n')}`)
      break
    }

    case '/projects': {
      const projects = await query<{ repo_name: string; momentum_score: number }>(
        `SELECT repo_name, momentum_score FROM projects ORDER BY momentum_score DESC LIMIT 10`
      )
      const lines = projects.map(
        p => `• <b>${p.repo_name}</b> — ${Math.round(p.momentum_score)}pts`
      )
      await send(chatId, `🚀 <b>Projects</b>\n\n${lines.join('\n')}`)
      break
    }

    case '/done': {
      const task = args.join(' ').trim()
      if (!task) { await send(chatId, 'Usage: /done <task description>'); break }
      await send(chatId, `✅ Logged: "<b>${task}</b>"`)
      break
    }

    default:
      await send(
        chatId,
        `Available commands:\n/focus [normal|low-energy|beast]\n/today\n/wins\n/ghost\n/projects\n/done &lt;task&gt;`
      )
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const message = body.message
    if (!message?.text) return NextResponse.json({ ok: true })

    await handleCommand(message.chat.id, message.text)
    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error('Telegram webhook error:', err)
    return NextResponse.json({ ok: true }) // always 200 to Telegram
  }
}
