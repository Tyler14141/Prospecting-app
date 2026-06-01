# Agentic OS

A coordinated AI agent team — a "command center" for founder/seller-led growth. Five Claude-powered agents share one Knowledge Vault and each own a slice of the revenue motion.

| Agent | Role | Model | Tools |
|-------|------|-------|-------|
| **CEO** (Avery Chen) | Orchestrator — strategy & delegation | `claude-opus-4-8` | adaptive thinking |
| **CMO** (Jordan Ellis) | Content & positioning | `claude-opus-4-8` | — |
| **Researcher** (Sam Rivera) | Market intelligence & prospecting | `claude-sonnet-4-6` | live web search |
| **Account Executive** (Morgan Diaz) | New-business outreach & qualification | `claude-sonnet-4-6` | — |
| **Account Manager** (Riley Brooks) | Retention & expansion | `claude-sonnet-4-6` | — |
| **Business Analyst** (Taylor Quinn) | Performance reporting & analytics | `claude-opus-4-8` | — |

## The agentic workforce (charters, roles, settings)

The team is a real org chart, not a chat panel. **10 agents**, each with a **charter** (mission, what it owns, KPIs, and who it hands work to/from) baked into its prompt:

CEO/Orchestrator · CMO · Researcher · **SDR** · AE · **Sales Engineer** · **Proposal & Grants Manager** · Account Manager · **RevOps** · Business Analyst.

- **Lifecycle & handoffs:** research → SDR → AE → SE/Proposal → AM, with RevOps and the Analyst supporting. The CEO sees the live roster and delegates by role.
- **Qualification scoring:** SDR/AE/RevOps can `score_lead` (0–100 fit) — shown as a colored badge on Lead Pipeline cards for prioritization/routing.
- **Goals / OKRs (Goals tab):** the CEO sets quotas (chat: “set our Q3 OKRs” → `set_goal` tool) or you add them in the UI. Most metrics (leads, qualified, meetings, won, win rate, content) **auto-track** from the pipeline with live % attainment; the Analyst reports against them and every agent sees the targets. Surfaced on the Command Center too.
- **Per-agent settings (Agent Console → Profile & Settings):** edit each agent's **job description**, **context**, **custom instructions / playbook**, and **model** — persisted (`/api/agents/config`) and injected into that agent's runs. The charter (mission/owns/KPIs/handoffs) is shown for reference.

## CRM, enrichment, two-way email & the daily brief

- **Salesforce sync** — saved leads auto-push to Salesforce when configured (`SALESFORCE_INSTANCE_URL` + `SALESFORCE_ACCESS_TOKEN`); a **Sync new → Salesforce** button on the Lead board pushes the backlog. Synced cards show a `✓ CRM` badge. Graceful no-op without creds.
- **Matcha enrichment** — the Researcher has a `matcha` tool that calls your internal contact tool (`MATCHA_API_URL` + `MATCHA_API_KEY`) to find real decision-makers with verified emails and attach the best one to a lead (`enriched` badge). Closes the "invented contacts" gap.
- **Two-way email** — the AE drafts outreach with a recipient (`to`); on approval an Email-channel draft is **actually sent** to the prospect. When a prospect **replies**, `/api/inbound` matches them to a lead, notifies you, and the AE drafts a suggested response into Needs Review.
- **Daily brief + reply-to-approve** — `/api/brief` (scheduled in `vercel.json`) emails you a morning digest: pipeline snapshot, numbered decisions awaiting review, and what's working. **Reply** "approve 1, 3" / "reject 2" / "approve all" and the inbound route applies it — no dashboard needed.
- **Closed-loop learning** — outcomes (win rate by product, content approval rate) are summarized and injected into every agent run, so targeting and messaging sharpen over time.
- **Calendar booking** — set `CALENDLY_URL` and agents include your scheduling link when proposing a call.

## Offload layer — run it without sitting in the dashboard

This is what turns the dashboard into a tool you delegate to:

- **Email the CEO** (`POST /api/inbound`) — point an email provider's inbound webhook (Postmark, SendGrid Inbound Parse, Mailgun routes, Cloudflare Email Workers) at this endpoint. It parses the message, runs the CEO orchestrator on it, and **emails you back** a summary (leads added, drafts awaiting review). Secure with `INBOUND_SECRET` (`?secret=` or `x-inbound-secret`) and optionally `INBOUND_ALLOWED_FROM` (sender allowlist).
- **Scheduled runs** (`/api/cron`) — a true server-side schedule (not just the tab-open auto-pilot). `vercel.json` runs it weekday mornings; it executes `CRON_WORKFLOWS` and emails you a digest. Works with any scheduler that can hit the URL; on Vercel Cron, `CRON_SECRET` is sent automatically.
- **Notifications back to you** — outbound replies + operator digests via `OPERATOR_EMAIL` (uses Resend; set `RESEND_API_KEY` + `MAIL_FROM`). No key = sending no-ops gracefully.
- **Gated outbound** — approving a draft in Needs Review emails it to you (the operator). Wire a real recipient/integration in `app/api/content/route.ts` to send to prospects.
- **Team memory** — agents have a `remember` tool; saved notes (preferences, decisions, account facts) are injected into every future run so you stop re-explaining context.
- **Trust & safety** — sender allowlist on inbound, per-run token usage in summaries, the Needs-Review approval gate, and the activity log.
- **Auth** — set `APP_PASSWORD` to put the dashboard + data APIs behind HTTP Basic auth (machine endpoints stay open for webhooks).

Quick local test of the inbound endpoint (once `ANTHROPIC_API_KEY` is set):

```bash
curl -X POST "http://localhost:3000/api/inbound?secret=$INBOUND_SECRET" \
  -H 'Content-Type: application/json' \
  -d '{"from":"you@example.com","subject":"Build TRIO pipeline","text":"Find 3 target cities and draft a LinkedIn post."}'
```

See `.env.example` for every variable.

## Workflows, analytics, activity & editable vault

- **Workflows** (Command Center) — one-click autonomous runs: *Scan for new leads*, *Draft this week's content*, *Draft outbound follow-up*, *Weekly scorecard*. Each fires an agent server-side; its tools populate the pipelines. **Auto-pilot** toggle re-runs lead scanning every 5 minutes while the tab is open.
- **Analytics** — lead funnel, content-by-stage, channel mix, win rate, and a full activity log (the Business Analyst's view).
- **Activity log** — every tool call, delegation, approval, and workflow run is recorded (`/api/activity`) and shown on the Command Center + Analytics.
- **Editable Knowledge Vault** — edit the shared context in-app and save (`/api/vault`); agents pick it up on their next run. Falls back to the built-in default until you customize it.

## Pipelines, review & tools

Agents don't just talk — they **act**. Specialists have real tools that write to a datastore:

- **Researcher / AE → `save_lead`** — drops a real, qualified prospect onto the **Lead Pipeline** board.
- **CMO / AE / AM → `create_content`** — sends a draft to the **Content Pipeline**, where it lands in **Needs Review**.

The **Lead Pipeline** and **Content Pipeline** are Kanban boards (move cards across stages). **Needs Review** is the human-in-the-loop gate: approve or reject agent drafts before they're marked done. The Command Center shows live counts (leads, needs-review, agents working). Everything streams in live — when the CEO delegates research, you watch leads appear on the board.

**Persistence:** leads and content are saved to `.data/db.json` (gitignored) via `lib/store.ts`, so they survive refreshes. On a read-only/serverless filesystem it falls back to in-memory; swap `lib/store.ts` for Postgres/KV for production.

## CEO delegation

The **CEO is a real orchestrator**, not just a planner. It has a `delegate` tool: when a request needs production work, the CEO hands concrete tasks to the right specialists, the server runs each one (with its own persona + tools — e.g. the Researcher's web search), streams their work into the chat, feeds it back to the CEO, and the CEO synthesizes a final answer. You see the hand-offs happen live (`▼ Delegated to … ▲ … done`). The CEO can delegate to several specialists in one turn.

## Stack

- **Next.js 14** (App Router) · **TypeScript** · **Tailwind CSS**
- **Anthropic Claude** — every model call is server-side (`app/api/chat`), so the API key never touches the browser
- **Streaming** responses + **prompt caching** on the shared Knowledge Vault

## Setup

```bash
npm install
cp .env.example .env.local   # then add your ANTHROPIC_API_KEY
npm run dev                  # http://localhost:3000
```

Get a key at https://console.anthropic.com.

## Project structure

```
app/
  api/chat/route.ts   ← streaming chat endpoint (per-agent system prompt + tools)
  page.tsx            ← Command Center, Agent Console, Knowledge Vault (single-page UI)
  layout.tsx, globals.css
lib/
  agents.ts           ← the 5 agent personas (model, tools, starter prompts)
  knowledge.ts        ← shared business context (company, products, ICP) → the Knowledge Vault
  anthropic.ts        ← Anthropic client
```

## Customizing

- **Re-point at your own business:** edit `lib/knowledge.ts` (company, products, ICP). It's injected into every agent's system prompt.
- **Tune an agent:** edit its `systemPersona`, `model`, or tools in `lib/agents.ts`.
- **Add an agent:** append to the `AGENTS` array — the sidebar, command center, and console pick it up automatically.

## Deploy (Vercel)

```bash
npm i -g vercel && vercel --prod
```

Add `ANTHROPIC_API_KEY` under **Project → Settings → Environment Variables**, then redeploy.
