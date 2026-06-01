'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { AGENTS, getAgent } from '@/lib/agents'
import { COMPANY, PRODUCTS, ICP } from '@/lib/knowledge'
import {
  LEAD_STAGES,
  CONTENT_STAGES,
  type Lead,
  type ContentItem,
  type LeadStage,
  type ContentStage,
} from '@/lib/pipeline'

type Role = 'user' | 'assistant'
interface Msg {
  role: Role
  content: string
}
type View = 'command' | 'console' | 'leads' | 'content' | 'review' | 'vault'
type Status = 'idle' | 'working'

function countOccurrences(haystack: string, needle: string): number {
  if (!needle) return 0
  let count = 0
  let idx = 0
  for (;;) {
    const i = haystack.indexOf(needle, idx)
    if (i === -1) break
    count++
    idx = i + needle.length
  }
  return count
}

// Read the CEO's delegation markers out of the live stream to know which
// specialists are mid-task (delegated but not yet "done").
function deriveWorking(text: string): string[] {
  return AGENTS.filter((a) => !a.canDelegate)
    .filter(
      (a) =>
        countOccurrences(text, `▼ Delegated to ${a.name}`) >
        countOccurrences(text, `▲ ${a.name} done`),
    )
    .map((a) => a.id)
}

const NAV: [View, string, string][] = [
  ['command', 'Command Center', '▦'],
  ['console', 'Agent Console', '✦'],
  ['leads', 'Lead Pipeline', '◫'],
  ['content', 'Content Pipeline', '✎'],
  ['review', 'Needs Review', '✔'],
  ['vault', 'Knowledge Vault', '▤'],
]

export default function Page() {
  const [view, setView] = useState<View>('command')
  const [activeId, setActiveId] = useState<string>(AGENTS[0].id)
  const [threads, setThreads] = useState<Record<string, Msg[]>>({})
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [statuses, setStatuses] = useState<Record<string, Status>>({})
  const [leads, setLeads] = useState<Lead[]>([])
  const [content, setContent] = useState<ContentItem[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  const active = getAgent(activeId)!
  const messages = threads[activeId] ?? []
  const totalConversations = Object.values(threads).filter((m) => m.length > 0).length
  const workingCount = Object.values(statuses).filter((s) => s === 'working').length
  const reviewCount = content.filter((c) => c.stage === 'review').length

  const refresh = useCallback(async () => {
    try {
      const [l, c] = await Promise.all([
        fetch('/api/leads').then((r) => r.json()),
        fetch('/api/content').then((r) => r.json()),
      ])
      setLeads(l.leads ?? [])
      setContent(c.content ?? [])
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh, view])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, view])

  function openConsole(id: string) {
    setActiveId(id)
    setView('console')
  }

  async function moveLead(id: string, stage: LeadStage) {
    setLeads((ls) => ls.map((l) => (l.id === id ? { ...l, stage } : l)))
    await fetch('/api/leads', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, patch: { stage } }),
    }).catch(() => {})
  }

  async function moveContent(id: string, stage: ContentStage) {
    setContent((cs) => cs.map((c) => (c.id === id ? { ...c, stage } : c)))
    await fetch('/api/content', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, patch: { stage } }),
    }).catch(() => {})
  }

  async function send(text: string) {
    const clean = text.trim()
    if (!clean || busy) return
    const id = activeId
    const history: Msg[] = [...(threads[id] ?? []), { role: 'user', content: clean }]
    setThreads((t) => ({ ...t, [id]: [...history, { role: 'assistant', content: '' }] }))
    setInput('')
    setBusy(true)
    setStatuses({ [id]: 'working' })

    const patchLast = (c: string) =>
      setThreads((t) => {
        const arr = [...(t[id] ?? [])]
        arr[arr.length - 1] = { role: 'assistant', content: c }
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
        const next: Record<string, Status> = { [id]: 'working' }
        for (const w of deriveWorking(acc)) next[w] = 'working'
        setStatuses(next)
      }
      if (!acc.trim()) patchLast('(no response)')
    } catch (err) {
      patchLast(`⚠️ ${err instanceof Error ? err.message : 'Something went wrong.'}`)
    } finally {
      setBusy(false)
      setStatuses({})
      refresh() // agents may have created leads / content this turn
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
          {NAV.map(([v, label, glyph]) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition ${
                view === v ? 'bg-white/10 text-white' : 'text-slate-300 hover:bg-white/5'
              }`}
            >
              <span className="opacity-70">{glyph}</span>
              {label}
              {v === 'review' && reviewCount > 0 && (
                <span className="ml-auto rounded-full bg-amber-400/20 px-1.5 text-[11px] font-medium text-amber-300">
                  {reviewCount}
                </span>
              )}
            </button>
          ))}
        </nav>

        <div className="mb-2 mt-6 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Agents
        </div>
        <div className="space-y-1 overflow-y-auto">
          {AGENTS.map((a) => {
            const working = (statuses[a.id] ?? 'idle') === 'working'
            return (
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
                  <span
                    className={`block truncate text-[11px] ${working ? 'text-amber-300' : 'text-slate-500'}`}
                  >
                    {working ? 'working…' : a.role.split('·')[0].trim()}
                  </span>
                </span>
                <span
                  className={`h-2 w-2 shrink-0 rounded-full shadow-[0_0_8px] ${
                    working
                      ? 'animate-pulse bg-amber-400 shadow-amber-400/70'
                      : 'bg-emerald-400 shadow-emerald-400/50'
                  }`}
                />
              </button>
            )
          })}
        </div>

        <div className="mt-auto px-3 pt-4 text-[11px] text-slate-500">
          <span className="inline-flex items-center gap-1.5">
            <span
              className={`h-2 w-2 rounded-full ${workingCount ? 'animate-pulse bg-amber-400' : 'bg-emerald-400'}`}
            />
            {workingCount ? `${workingCount} working…` : `System live · ${AGENTS.length} agents`}
          </span>
        </div>
      </aside>

      {/* Main */}
      <main className="flex min-w-0 flex-1 flex-col">
        {view === 'command' && (
          <CommandCenter
            totalConversations={totalConversations}
            statuses={statuses}
            leadCount={leads.length}
            reviewCount={reviewCount}
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
                {statuses[activeId] === 'working' && (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/30 px-2.5 py-1 text-[11px] text-amber-300">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400" /> working
                  </span>
                )}
                <span className="rounded-full border border-white/10 px-2.5 py-1 text-[11px] text-slate-400">
                  {active.model}
                </span>
                {active.webSearch && (
                  <span className="rounded-full border border-cyan-400/30 px-2.5 py-1 text-[11px] text-cyan-300">
                    web search
                  </span>
                )}
                {active.canDelegate && (
                  <span className="rounded-full border border-amber-400/30 px-2.5 py-1 text-[11px] text-amber-300">
                    delegates
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

        {view === 'leads' && <LeadBoard leads={leads} onMove={moveLead} />}
        {view === 'content' && <ContentBoard content={content} onMove={moveContent} />}
        {view === 'review' && <ReviewQueue content={content} onMove={moveContent} />}
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
  statuses,
  leadCount,
  reviewCount,
  onOpen,
}: {
  totalConversations: number
  statuses: Record<string, 'idle' | 'working'>
  leadCount: number
  reviewCount: number
  onOpen: (id: string) => void
}) {
  const workingCount = Object.values(statuses).filter((s) => s === 'working').length
  const metrics = [
    { label: 'Working now', value: String(workingCount), sub: workingCount ? 'live' : 'idle' },
    { label: 'Leads in pipeline', value: String(leadCount), sub: 'saved by agents' },
    { label: 'Needs review', value: String(reviewCount), sub: 'awaiting approval' },
    { label: 'Conversations', value: String(totalConversations), sub: 'this session' },
  ]
  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-cyan-400">
          Agentic Growth System
        </div>
        <h1 className="text-2xl font-semibold">Command Center</h1>
        <p className="mt-1 text-sm text-slate-400">
          A coordinated AI agent team for {COMPANY.name}. Chat with any agent to put it to work —
          their leads and content land in the pipelines.
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
          {AGENTS.map((a) => {
            const working = (statuses[a.id] ?? 'idle') === 'working'
            return (
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
                  <span
                    className={`ml-auto h-2 w-2 rounded-full ${
                      working
                        ? 'animate-pulse bg-amber-400 shadow-[0_0_8px] shadow-amber-400/70'
                        : 'bg-emerald-400'
                    }`}
                  />
                </div>
                <p className="mt-3 text-xs leading-relaxed text-slate-400">{a.blurb}</p>
                <div
                  className="mt-3 text-[11px] font-medium"
                  style={{ color: working ? '#fbbf24' : a.accent }}
                >
                  {working ? 'Working…' : 'Open console →'}
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function BoardHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="border-b border-white/10 px-6 py-4">
      <h1 className="text-lg font-semibold">{title}</h1>
      <p className="text-xs text-slate-400">{subtitle}</p>
    </div>
  )
}

function EmptyHint({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid flex-1 place-items-center px-6 text-center">
      <p className="max-w-sm text-sm text-slate-500">{children}</p>
    </div>
  )
}

function LeadBoard({ leads, onMove }: { leads: Lead[]; onMove: (id: string, s: LeadStage) => void }) {
  return (
    <section className="flex min-h-0 flex-1 flex-col">
      <BoardHeader
        title="Lead Pipeline"
        subtitle="Prospects saved by the Researcher and AE. Move cards as deals progress."
      />
      {leads.length === 0 ? (
        <EmptyHint>
          No leads yet. Ask the <strong className="text-slate-300">Researcher</strong> to find
          prospects (it can save them straight to this board).
        </EmptyHint>
      ) : (
        <div className="flex min-h-0 flex-1 gap-3 overflow-x-auto px-6 py-5">
          {LEAD_STAGES.map((stage, si) => {
            const cards = leads.filter((l) => l.stage === stage.key)
            return (
              <div key={stage.key} className="flex w-72 shrink-0 flex-col">
                <div className="mb-2 flex items-center justify-between px-1 text-xs font-semibold text-slate-300">
                  <span>{stage.label}</span>
                  <span className="text-slate-500">{cards.length}</span>
                </div>
                <div className="space-y-2">
                  {cards.map((l) => (
                    <div
                      key={l.id}
                      className="rounded-xl border border-white/10 bg-white/[0.03] p-3"
                    >
                      <div className="text-sm font-semibold">{l.org}</div>
                      {l.location && <div className="text-[11px] text-slate-500">{l.location}</div>}
                      {(l.contact || l.title) && (
                        <div className="mt-1 text-xs text-slate-300">
                          {l.contact}
                          {l.contact && l.title ? ' · ' : ''}
                          <span className="text-slate-400">{l.title}</span>
                        </div>
                      )}
                      {l.product && (
                        <span className="mt-2 inline-block rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-slate-300">
                          {l.product}
                        </span>
                      )}
                      {l.whyFit && <p className="mt-2 text-[11px] leading-snug text-slate-500">{l.whyFit}</p>}
                      <div className="mt-3 flex justify-between text-[11px]">
                        <button
                          disabled={si === 0}
                          onClick={() => onMove(l.id, LEAD_STAGES[si - 1].key)}
                          className="text-slate-400 hover:text-slate-200 disabled:opacity-30"
                        >
                          ◀ back
                        </button>
                        <button
                          disabled={si === LEAD_STAGES.length - 1}
                          onClick={() => onMove(l.id, LEAD_STAGES[si + 1].key)}
                          className="text-cyan-300 hover:text-cyan-200 disabled:opacity-30"
                        >
                          advance ▶
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

function ContentBoard({
  content,
  onMove,
}: {
  content: ContentItem[]
  onMove: (id: string, s: ContentStage) => void
}) {
  const visible = content.filter((c) => c.stage !== 'rejected')
  return (
    <section className="flex min-h-0 flex-1 flex-col">
      <BoardHeader
        title="Content Pipeline"
        subtitle="Drafts from the CMO, AE, and AM. They start in Review until you approve them."
      />
      {visible.length === 0 ? (
        <EmptyHint>
          No content yet. Ask the <strong className="text-slate-300">CMO</strong> to write posts or
          the <strong className="text-slate-300">AE</strong> to draft outreach.
        </EmptyHint>
      ) : (
        <div className="flex min-h-0 flex-1 gap-3 overflow-x-auto px-6 py-5">
          {CONTENT_STAGES.map((stage, si) => {
            const cards = visible.filter((c) => c.stage === stage.key)
            return (
              <div key={stage.key} className="flex w-72 shrink-0 flex-col">
                <div className="mb-2 flex items-center justify-between px-1 text-xs font-semibold text-slate-300">
                  <span>{stage.label}</span>
                  <span className="text-slate-500">{cards.length}</span>
                </div>
                <div className="space-y-2">
                  {cards.map((c) => (
                    <div
                      key={c.id}
                      className="rounded-xl border border-white/10 bg-white/[0.03] p-3"
                    >
                      <div className="flex items-center gap-2">
                        <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-slate-300">
                          {c.channel}
                        </span>
                        {c.product && <span className="text-[10px] text-slate-500">{c.product}</span>}
                      </div>
                      <div className="mt-1.5 text-sm font-semibold">{c.title}</div>
                      <p className="mt-1 line-clamp-4 whitespace-pre-wrap text-[11px] leading-snug text-slate-400">
                        {c.body}
                      </p>
                      <div className="mt-3 flex justify-between text-[11px]">
                        <button
                          disabled={si === 0}
                          onClick={() => onMove(c.id, CONTENT_STAGES[si - 1].key)}
                          className="text-slate-400 hover:text-slate-200 disabled:opacity-30"
                        >
                          ◀ back
                        </button>
                        <button
                          disabled={si === CONTENT_STAGES.length - 1}
                          onClick={() => onMove(c.id, CONTENT_STAGES[si + 1].key)}
                          className="text-cyan-300 hover:text-cyan-200 disabled:opacity-30"
                        >
                          advance ▶
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

function ReviewQueue({
  content,
  onMove,
}: {
  content: ContentItem[]
  onMove: (id: string, s: ContentStage) => void
}) {
  const pending = content.filter((c) => c.stage === 'review')
  return (
    <section className="flex min-h-0 flex-1 flex-col">
      <BoardHeader
        title="Needs Review"
        subtitle="Human-in-the-loop: approve or reject what the agents drafted before it ships."
      />
      {pending.length === 0 ? (
        <EmptyHint>Nothing waiting. Agent drafts will appear here for your approval.</EmptyHint>
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
          <div className="mx-auto max-w-2xl space-y-3">
            {pending.map((c) => (
              <div key={c.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-slate-300">
                    {c.channel}
                  </span>
                  <span className="text-sm font-semibold">{c.title}</span>
                  {c.product && <span className="text-[10px] text-slate-500">{c.product}</span>}
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-200">
                  {c.body}
                </p>
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => onMove(c.id, 'approved')}
                    className="rounded-lg bg-emerald-500/90 px-3 py-1.5 text-xs font-medium text-slate-900 hover:bg-emerald-400"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => onMove(c.id, 'rejected')}
                    className="rounded-lg border border-white/15 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/5"
                  >
                    ✕ Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}

function Vault() {
  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Knowledge Vault</h1>
        <p className="mt-1 text-sm text-slate-400">
          The shared context every agent reasons from. Edit{' '}
          <code className="text-slate-300">lib/knowledge.ts</code> to re-point the OS at a different
          company, products, or ICP.
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
