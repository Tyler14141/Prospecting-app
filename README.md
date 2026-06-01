# Agentic OS

A coordinated AI agent team — a "command center" for founder/seller-led growth. Five Claude-powered agents share one Knowledge Vault and each own a slice of the revenue motion.

| Agent | Role | Model | Tools |
|-------|------|-------|-------|
| **CEO** (Avery Chen) | Orchestrator — strategy & delegation | `claude-opus-4-8` | adaptive thinking |
| **CMO** (Jordan Ellis) | Content & positioning | `claude-sonnet-4-6` | — |
| **Researcher** (Sam Rivera) | Market intelligence & prospecting | `claude-sonnet-4-6` | live web search |
| **Account Executive** (Morgan Diaz) | New-business outreach & qualification | `claude-sonnet-4-6` | — |
| **Account Manager** (Riley Brooks) | Retention & expansion | `claude-sonnet-4-6` | — |
| **Business Analyst** (Taylor Quinn) | Performance reporting & analytics | `claude-sonnet-4-6` | — |

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
