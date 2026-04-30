import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = { title: 'Focus Engine' }

const nav = [
  { href: '/',           label: '🎯 Today' },
  { href: '/status',     label: '📊 Status' },
  { href: '/activity',   label: '📈 Activity' },
  { href: '/drafts',     label: '✍️ Drafts' },
  { href: '/portfolio',  label: '🗂 Portfolio' },
]

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100 min-h-screen font-mono">
        <nav className="border-b border-zinc-800 px-6 py-3 flex gap-6 text-sm">
          {nav.map(({ href, label }) => (
            <Link key={href} href={href} className="text-zinc-400 hover:text-white transition-colors">
              {label}
            </Link>
          ))}
        </nav>
        <main className="px-6 py-8 max-w-4xl mx-auto">{children}</main>
      </body>
    </html>
  )
}
