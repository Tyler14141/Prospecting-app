'use client'

import { useEffect, useRef, useState } from 'react'
import { AGENTS, getAgent } from '@/lib/agents'
import { COMPANY, PRODUCTS, ICP } from '@/lib/knowledge'

type Role = 'user' | 'assistant'
interface Msg {
  role: Role
  content: string
}
type View = 'command' | 'console' | 'vault'

export default function Page() {
  const [view, setView] = useState<View>('command')
  const [activeId, setActiveId] = useState<string>(AGENTS[0].id)
  const [threads, setThreads] = useState<Record<string, Msg[]>>({})
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const active = getAgent(activeId)!
  const messages = threads[activeId] ?? []
  const totalConversations = Object.values(threads).filter((m) => m.length > 0).length

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, view])

  function openConsole(id: string) {
    setActiveId(id)
    setView('console')
  }

  async function send(text: string) {
    const clean = text.trim()
    if (!clean || busy) return
    const id = activeId
    const history: Msg[] = [...(threads[id] ?? []), { role: 'user', content: clean }]
    setThreads((t) => ({ ...t, [id]: [...history, { role: 'assistant', content: '' }] }))
    setInput('')
    setBusy(true)

    const patchLast = (content: string) =>
      setThreads((t) => {
        const arr = [...(t[id] ?? [])]
        arr[arr.length - 1] = { role: 'assistant', content }
        return { ...t, [id]: arr }
      })

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agentId: id, messages: history }),
      })
      if (!res.ok || !res.body) {
        const e = await res.json().catch(() => ({}))
        throw new Error(e.error || `Request failed (${res.status})`)
      }
      const reader = res.body.getReader()
      const dec = new TextDecoder()
      let acc = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        acc += dec.decode(value, { stream: true })
        patchLast(acc)
      }
      if (!acc.trim()) patchLast('(no response)')
    } catch (err) {
      patchLast(`⚠️ ${err instanceof Error ? err.message : 'Something went wrong.'}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-64 shrink-0 flex-col border-r border-white/10 bg-black/20 px-3 py-4">
        <div className="mb-6 flex items-center gap-2 px-2">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-cyan-400 to-violet-500 font-bold text-slate-900">
            OS
          </div>
          <div>
            <div className="text-sm font-semibold leading-tight">Agentic OS</div>
            <div className="text-[11px] text-slate-400">Agentic growth ops</div>
          </div>
        </div>

        <nav className="space-y-1">
          {(
            [
              ['command', 'Command Center', '▦'],
              ['console', 'Agent Console', '✦'],
              ['vault', 'Knowledge Vault', '▤'],
            ] as [View, string, string][]
          ).map(([v, label, glyph]) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition ${
                view === v ? 'bg-white/10 text-white' : 'text-slate-300 hover:bg-white/5'
              }`}
            >
              <span className="opacity-70">{glyph}</span>
              {label}
            </button>
          ))}
        </nav>

        <div className="mb-2 mt-6 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Agents
        </div>
        <div className="space-y-1 overflow-y-auto">
          {AGENTS.map((a) => (
            <button
              key={a.id}
              onClick={() => openConsole(a.id)}
              className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition ${
                view === 'console' && activeId === a.id ? 'bg-white/10' : 'hover:bg-white/5'
              }`}
            >
              <span
                className="grid h-7 w-7 shrink-0 place-items-center rounded-md text-sm"
                style={{ background: `${a.accent}22`, color: a.accent }}
              >
                {a.icon}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[13px] text-slate-200">{a.name}</span>
                <span className="block truncate text-[11px] text-slate-500">
                  {a.role.split('·')[0].trim()}
                </span>
              </span>
              <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-400 shadow-[0_0_8px] shadow-emerald-400/60" />
            </button>
          ))}
        </div>

        <div className="mt-auto px-3 pt-4 text-[11px] text-slate-500">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400" /> System live · {AGENTS.length} agents
          </span>
        </div>
      </aside>

      {/* Main */}
      <main className="flex min-w-0 flex-1 flex-col">
        {view === 'command' && (
          <CommandCenter
            totalConversations={totalConversations}
            onOpen={openConsole}
          />
        )}

        {view === 'console' && (
          <section className="flex min-h-0 flex-1 flex-col">
            <header
              className="flex items-center gap-3 border-b border-white/10 px-6 py-4"
              style={{ background: `linear-gradient(90deg, ${active.accent}14, transparent)` }}
            >
              <span
                className="grid h-10 w-10 place-items-center rounded-lg text-lg"
                style={{ background: `${active.accent}22`, color: active.accent }}
              >
                {active.icon}
              </span>
              <div className="min-w-0">
                <h2 className="truncate text-base font-semibold">{active.name}</h2>
                <p className="truncate text-xs text-slate-400">{active.role}</p>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <span className="rounded-full border border-white/10 px-2.5 py-1 text-[11px] text-slate-400">
                  {active.model}
                </span>
                {active.webSearch && (
                  <span className="rounded-full border border-cyan-400/30 px-2.5 py-1 text-[11px] text-cyan-300">
                    web search
                  </span>
                )}
                {active.thinking && (
                  <span className="rounded-full border border-amber-400/30 px-2.5 py-1 text-[11px] text-amber-300">
                    thinking
                  </span>
                )}
              </div>
            </header>

            <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
              {messages.length === 0 ? (
                <div className="mx-auto max-w-2xl">
                  <p className="mb-1 text-sm text-slate-300">{active.blurb}</p>
                  <p className="mb-4 text-xs text-slate-500">Try one of these to get started:</p>
                  <div className="grid gap-2">
                    {active.starters.map((s) => (
                      <button
                        key={s}
                        onClick={() => send(s)}
                        className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-left text-sm text-slate-200 transition hover:border-white/20 hover:bg-white/[0.06]"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="mx-auto max-w-2xl space-y-4">
                  {messages.map((m, i) => (
                    <Bubble key={i} msg={m} accent={active.accent} icon={active.icon} />
                  ))}
                </div>
              )}
            </div>

            <div className="border-t border-white/10 px-6 py-4">
              <div className="mx-auto flex max-w-2xl items-end gap-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      send(input)
                    }
                  }}
                  rows={1}
                  placeholder={`Message ${active.name}…`}
                  className="max-h-40 min-h-[44px] flex-1 resize-none rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-white/25"
                />
                <button
                  onClick={() => send(input)}
                  disabled={busy || !input.trim()}
                  className="h-11 shrink-0 rounded-xl px-5 text-sm font-medium text-slate-900 transition disabled:cursor-not-allowed disabled:opacity-40"
                  style={{ background: active.accent }}
                >
                  {busy ? '…' : 'Send'}
                </button>
              </div>
            </div>
          </section>
        )}

        {view === 'vault' && <Vault />}
      </main>
    </div>
  )
}

function Bubble({ msg, accent, icon }: { msg: Msg; accent: string; icon: string }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <span
        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-sm"
        style={
          isUser
            ? { background: 'rgba(148,163,184,0.18)', color: '#cbd5e1' }
            : { background: `${accent}22`, color: accent }
        }
      >
        {isUser ? 'You' : icon}
      </span>
      <div
        className={`whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser ? 'bg-white/10 text-slate-100' : 'border border-white/10 bg-white/[0.03] text-slate-200'
        }`}
        style={{ maxWidth: '85%' }}
      >
        {msg.content || <span className="text-slate-500">▍</span>}
      </div>
    </div>
  )
}

function CommandCenter({
  totalConversations,
  onOpen,
}: {
  totalConversations: number
  onOpen: (id: string) => void
}) {
  const metrics = [
    { label: 'Agents online', value: String(AGENTS.length), sub: 'CEO + 4 specialists' },
    { label: 'Active conversations', value: String(totalConversations), sub: 'this session' },
    { label: 'Product lines', value: String(PRODUCTS.length), sub: 'in the knowledge vault' },
    { label: 'Monitoring', value: '24/7', sub: 'always-on' },
  ]
  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-cyan-400">
          Agentic Growth System
        </div>
        <h1 className="text-2xl font-semibold">Command Center</h1>
        <p className="mt-1 text-sm text-slate-400">
          A coordinated AI agent team for {COMPANY.name}. Chat with any agent to put it to work.
        </p>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {metrics.map((m) => (
            <div key={m.label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="text-[11px] uppercase tracking-wide text-slate-500">{m.label}</div>
              <div className="mt-1 text-2xl font-semibold">{m.value}</div>
              <div className="text-[11px] text-slate-500">{m.sub}</div>
            </div>
          ))}
        </div>

        <h2 className="mb-3 mt-8 text-sm font-semibold text-slate-300">Your team</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {AGENTS.map((a) => (
            <button
              key={a.id}
              onClick={() => onOpen(a.id)}
              className="group rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:-translate-y-0.5 hover:border-white/20 hover:bg-white/[0.06]"
            >
              <div className="flex items-center gap-3">
                <span
                  className="grid h-10 w-10 place-items-center rounded-lg text-lg"
                  style={{ background: `${a.accent}22`, color: a.accent }}
                >
                  {a.icon}
                </span>
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold">{a.name}</div>
                  <div className="truncate text-[11px] text-slate-500">{a.role}</div>
                </div>
                <span className="ml-auto h-2 w-2 rounded-full bg-emerald-400" />
              </div>
              <p className="mt-3 text-xs leading-relaxed text-slate-400">{a.blurb}</p>
              <div className="mt-3 text-[11px] font-medium" style={{ color: a.accent }}>
                Open console →
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function Vault() {
  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Knowledge Vault</h1>
        <p className="mt-1 text-sm text-slate-400">
          The shared context every agent reasons from. Edit <code className="text-slate-300">lib/knowledge.ts</code>{' '}
          to re-point the OS at a different company, products, or ICP.
        </p>

        <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <div className="text-sm font-semibold">{COMPANY.name}</div>
          <p className="mt-1 text-xs leading-relaxed text-slate-400">{COMPANY.description}</p>
        </div>

        <h2 className="mb-3 mt-6 text-sm font-semibold text-slate-300">Product lines</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {PRODUCTS.map((p) => (
            <div key={p.key} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="text-sm font-semibold">{p.name}</div>
              <p className="mt-1 text-xs text-slate-400">{p.oneLiner}</p>
              <p className="mt-2 text-[11px] text-slate-500">
                <span className="text-slate-400">Buyers:</span> {p.buyers.join(', ')}
              </p>
            </div>
          ))}
        </div>

        <h2 className="mb-3 mt-6 text-sm font-semibold text-slate-300">Ideal Customer Profile</h2>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <p className="text-xs text-slate-400">
            <span className="text-slate-300">Segment:</span> {ICP.segment}
          </p>
          <p className="mt-2 text-xs text-slate-400">
            <span className="text-slate-300">Size:</span> {ICP.size}
          </p>
          <ul className="mt-3 space-y-1">
            {ICP.triggers.map((t) => (
              <li key={t} className="flex gap-2 text-xs text-slate-400">
                <span className="text-cyan-400">▹</span>
                {t}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
