'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { AGENTS, getAgent } from '@/lib/agents'
import { COMPANY, PRODUCTS, ICP } from '@/lib/knowledge'
import { WORKFLOWS, getWorkflow } from '@/lib/workflows'
import {
  LEAD_STAGES,
  CONTENT_STAGES,
  type Lead,
  type ContentItem,
  type ActivityEvent,
  type LeadStage,
  type ContentStage,
} from '@/lib/pipeline'

type Role = 'user' | 'assistant'
interface Msg {
  role: Role
  content: string
}
type View = 'command' | 'console' | 'leads' | 'content' | 'review' | 'analytics' | 'vault'
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

function deriveWorking(text: string): string[] {
  return AGENTS.filter((a) => !a.canDelegate)
    .filter(
      (a) =>
        countOccurrences(text, `▼ Delegated to ${a.name}`) >
        countOccurrences(text, `▲ ${a.name} done`),
    )
    .map((a) => a.id)
}

function agentMeta(id?: string) {
  const a = id ? getAgent(id) : undefined
  return a
    ? { name: a.name, accent: a.accent, icon: a.icon }
    : { name: 'System', accent: '#94a3b8', icon: '•' }
}

function fmtTime(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

const NAV: [View, string, string][] = [
  ['command', 'Command Center', '▦'],
  ['console', 'Agent Console', '✦'],
  ['leads', 'Lead Pipeline', '◫'],
  ['content', 'Content Pipeline', '✎'],
  ['review', 'Needs Review', '✔'],
  ['analytics', 'Analytics', '▥'],
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
  const [activity, setActivity] = useState<ActivityEvent[]>([])
  const [runningWf, setRunningWf] = useState<Record<string, boolean>>({})
  const [autopilot, setAutopilot] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const active = getAgent(activeId)!
  const messages = threads[activeId] ?? []
  const totalConversations = Object.values(threads).filter((m) => m.length > 0).length
  const workingCount = Object.values(statuses).filter((s) => s === 'working').length
  const reviewCount = content.filter((c) => c.stage === 'review').length

  const refresh = useCallback(async () => {
    try {
      const [l, c, a] = await Promise.all([
        fetch('/api/leads').then((r) => r.json()),
        fetch('/api/content').then((r) => r.json()),
        fetch('/api/activity').then((r) => r.json()),
      ])
      setLeads(l.leads ?? [])
      setContent(c.content ?? [])
      setActivity(a.activity ?? [])
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

  const runWorkflow = useCallback(
    async (id: string) => {
      const wf = getWorkflow(id)
      if (!wf || runningWf[id]) return
      setRunningWf((r) => ({ ...r, [id]: true }))
      setStatuses((s) => ({ ...s, [wf.agentId]: 'working' }))
      try {
        await fetch('/api/workflows/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id }),
        })
      } catch {
        /* ignore */
      } finally {
        setRunningWf((r) => ({ ...r, [id]: false }))
        setStatuses((s) => {
          const n = { ...s }
          delete n[wf.agentId]
          return n
        })
        refresh()
      }
    },
    [runningWf, refresh],
  )

  // Auto-pilot: while on (and the tab is open), scan for leads every 5 minutes.
  useEffect(() => {
    if (!autopilot) return
    const t = setInterval(() => runWorkflow('scan-leads'), 5 * 60 * 1000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autopilot])

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
    refresh()
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
      refresh()
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
            activity={activity}
            runningWf={runningWf}
            autopilot={autopilot}
            onToggleAutopilot={() => setAutopilot((v) => !v)}
            onRun={runWorkflow}
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
        {view === 'analytics' && <Analytics leads={leads} content={content} activity={activity} />}
        {view === 'vault' && <VaultEditor />}
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

function ActivityFeed({ activity }: { activity: ActivityEvent[] }) {
  if (activity.length === 0) {
    return <p className="text-xs text-slate-500">No activity yet. Put an agent to work.</p>
  }
  return (
    <div className="space-y-2">
      {activity.map((e) => {
        const m = agentMeta(e.agentId)
        return (
          <div key={e.id} className="flex items-start gap-2.5 text-xs">
            <span
              className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md text-[11px]"
              style={{ background: `${m.accent}22`, color: m.accent }}
            >
              {m.icon}
            </span>
            <div className="min-w-0 flex-1">
              <span className="text-slate-300">{e.message}</span>
              <span className="ml-1.5 text-slate-600">· {m.name}</span>
            </div>
            <span className="shrink-0 text-[11px] text-slate-600">{fmtTime(e.ts)}</span>
          </div>
        )
      })}
    </div>
  )
}

function CommandCenter({
  totalConversations,
  statuses,
  leadCount,
  reviewCount,
  activity,
  runningWf,
  autopilot,
  onToggleAutopilot,
  onRun,
  onOpen,
}: {
  totalConversations: number
  statuses: Record<string, 'idle' | 'working'>
  leadCount: number
  reviewCount: number
  activity: ActivityEvent[]
  runningWf: Record<string, boolean>
  autopilot: boolean
  onToggleAutopilot: () => void
  onRun: (id: string) => void
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
          A coordinated AI agent team for {COMPANY.name}. Chat with an agent or run a workflow —
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

        {/* Workflows */}
        <div className="mb-3 mt-8 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-300">Workflows</h2>
          <button
            onClick={onToggleAutopilot}
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] transition ${
              autopilot
                ? 'border-amber-400/40 bg-amber-400/10 text-amber-300'
                : 'border-white/10 text-slate-400 hover:bg-white/5'
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${autopilot ? 'animate-pulse bg-amber-400' : 'bg-slate-500'}`}
            />
            {autopilot ? 'Auto-pilot on · scans every 5 min' : 'Auto-pilot off'}
          </button>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {WORKFLOWS.map((w) => {
            const a = getAgent(w.agentId)
            const running = !!runningWf[w.id]
            return (
              <div key={w.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex items-center gap-2">
                  {a && (
                    <span
                      className="grid h-7 w-7 place-items-center rounded-md text-sm"
                      style={{ background: `${a.accent}22`, color: a.accent }}
                    >
                      {a.icon}
                    </span>
                  )}
                  <div className="text-sm font-semibold">{w.name}</div>
                  <button
                    onClick={() => onRun(w.id)}
                    disabled={running}
                    className="ml-auto rounded-lg border border-white/15 px-3 py-1 text-[11px] text-slate-200 transition hover:bg-white/5 disabled:opacity-50"
                  >
                    {running ? 'Running…' : 'Run ▷'}
                  </button>
                </div>
                <p className="mt-2 text-xs text-slate-400">{w.description}</p>
              </div>
            )
          })}
        </div>

        {/* Team + Activity */}
        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
          <div>
            <h2 className="mb-3 text-sm font-semibold text-slate-300">Your team</h2>
            <div className="grid gap-3 sm:grid-cols-2">
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

          <div>
            <h2 className="mb-3 text-sm font-semibold text-slate-300">Recent activity</h2>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <ActivityFeed activity={activity.slice(0, 8)} />
            </div>
          </div>
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
          prospects, or run the “Scan for new leads” workflow.
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
                    <div key={l.id} className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
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
                      {l.whyFit && (
                        <p className="mt-2 text-[11px] leading-snug text-slate-500">{l.whyFit}</p>
                      )}
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
          run the “Draft this week’s content” workflow.
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
                    <div key={c.id} className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
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

function Bar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div>
      <div className="flex justify-between text-[11px] text-slate-400">
        <span>{label}</span>
        <span className="text-slate-300">{value}</span>
      </div>
      <div className="mt-1 h-2 rounded bg-white/5">
        <div className="h-2 rounded" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

function Analytics({
  leads,
  content,
  activity,
}: {
  leads: Lead[]
  content: ContentItem[]
  activity: ActivityEvent[]
}) {
  const leadCounts = LEAD_STAGES.map((s) => leads.filter((l) => l.stage === s.key).length)
  const leadMax = Math.max(1, ...leadCounts)
  const contentCounts = CONTENT_STAGES.map((s) => content.filter((c) => c.stage === s.key).length)
  const contentMax = Math.max(1, ...contentCounts)
  const won = leads.filter((l) => l.stage === 'won').length
  const conv = leads.length ? Math.round((won / leads.length) * 100) : 0
  const channels = Array.from(new Set(content.map((c) => c.channel)))

  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-4xl">
        <h1 className="text-2xl font-semibold">Analytics</h1>
        <p className="mt-1 text-sm text-slate-400">
          Performance across the pipeline — the Business Analyst’s view of the system.
        </p>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: 'Total leads', value: String(leads.length) },
            { label: 'Won', value: String(won) },
            { label: 'Win rate', value: `${conv}%` },
            { label: 'Content pieces', value: String(content.length) },
          ].map((m) => (
            <div key={m.label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="text-[11px] uppercase tracking-wide text-slate-500">{m.label}</div>
              <div className="mt-1 text-2xl font-semibold">{m.value}</div>
            </div>
          ))}
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-300">Lead funnel</h2>
            <div className="space-y-3">
              {LEAD_STAGES.map((s, i) => (
                <Bar key={s.key} label={s.label} value={leadCounts[i]} max={leadMax} color="#38bdf8" />
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-300">Content by stage</h2>
            <div className="space-y-3">
              {CONTENT_STAGES.map((s, i) => (
                <Bar key={s.key} label={s.label} value={contentCounts[i]} max={contentMax} color="#a78bfa" />
              ))}
            </div>
            {channels.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-1.5">
                {channels.map((ch) => (
                  <span
                    key={ch}
                    className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-slate-300"
                  >
                    {ch}: {content.filter((c) => c.channel === ch).length}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-300">Activity log</h2>
          <ActivityFeed activity={activity.slice(0, 30)} />
        </div>
      </div>
    </div>
  )
}

function VaultEditor() {
  const [text, setText] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [isDefault, setIsDefault] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetch('/api/vault')
      .then((r) => r.json())
      .then((d) => {
        setText(d.text ?? '')
        setIsDefault(!!d.isDefault)
        setLoaded(true)
      })
      .catch(() => setLoaded(true))
  }, [])

  async function save() {
    setSaving(true)
    setSaved(false)
    try {
      await fetch('/api/vault', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      setIsDefault(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch {
      /* ignore */
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Knowledge Vault</h1>
        <p className="mt-1 text-sm text-slate-400">
          The shared context every agent reasons from. Edit it here and save — changes take effect on
          the next agent run. {isDefault ? 'Currently using the built-in default.' : 'Custom vault saved.'}
        </p>

        <textarea
          value={loaded ? text : 'Loading…'}
          onChange={(e) => setText(e.target.value)}
          disabled={!loaded}
          rows={20}
          className="mt-4 w-full resize-y rounded-2xl border border-white/10 bg-black/30 p-4 font-mono text-xs leading-relaxed text-slate-200 outline-none focus:border-white/25"
        />
        <div className="mt-3 flex items-center gap-3">
          <button
            onClick={save}
            disabled={saving || !loaded}
            className="rounded-xl bg-cyan-400 px-5 py-2 text-sm font-medium text-slate-900 transition hover:bg-cyan-300 disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save vault'}
          </button>
          {saved && <span className="text-xs text-emerald-400">Saved ✓</span>}
        </div>

        <h2 className="mb-3 mt-8 text-sm font-semibold text-slate-300">Product reference</h2>
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

        <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-xs text-slate-400">
          <span className="text-slate-300">ICP:</span> {ICP.segment} — {ICP.size}
        </div>
      </div>
    </div>
  )
}
