# Harris Prospecting Agent

ICP-driven market research → real municipal contact sourcing → personalized 3-touch email cadences → outcome tracking.

## Stack

- **Next.js 14** (App Router)
- **TypeScript + Tailwind CSS**
- **Anthropic Claude** — all API calls are server-side (key never touches the browser)

---

## Local Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Add your Anthropic API key

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:

```
ANTHROPIC_API_KEY=sk-ant-your-real-key-here
```

Get a key at https://console.anthropic.com

### 3. Run locally

```bash
npm run dev
```

Open http://localhost:3000

---

## Deploy to Vercel

```bash
npm install -g vercel
vercel login
vercel --prod
```

Then add your API key in the Vercel dashboard:
**Project → Settings → Environment Variables → ANTHROPIC_API_KEY**

Redeploy once after adding the key.

---

## How it works

| Step | What happens |
|------|-------------|
| **1. ICP Setup** | Pick product, country, states/provinces, population range, and target titles |
| **2. Market Research** | Live web search finds 6 real municipalities matching your ICP |
| **3. Real Contacts** | Searches each municipality's official website for real staff names, titles, and emails |
| **4. Email Cadence** | Writes a personalized 3-touch sequence per contact (Day 1 intro / Day 5 follow-up / Day 12 breakup) |
| **Tracking tab** | Log status per contact, add notes, export CSV |

---

## Tracking persistence

Tracking data is stored in `.tracking-db.json` at the project root — works perfectly locally.

On Vercel's free tier the filesystem is ephemeral between deployments. For permanent cloud persistence, swap the file store in `app/api/tracking/route.ts` for **Vercel Postgres** (`npm install @vercel/postgres`). Tell Claude Code: *"Replace the file-based tracking store with Vercel Postgres"* and it will handle the migration.

---

## Project structure

```
app/
  api/
    research/route.ts     ← web search for municipalities
    contacts/route.ts     ← municipal website contact lookup
    cadence/route.ts      ← 3-touch email generation
    tracking/route.ts     ← CRUD for tracked contacts
  page.tsx                ← main UI (all 4 steps + tracking tab)
  layout.tsx
  globals.css
components/
  Stepper.tsx
  RegionPicker.tsx
  PopulationSlider.tsx
  ChipInput.tsx
  TrackingTable.tsx
lib/
  constants.ts            ← product data, region data, status labels
  types.ts                ← shared TypeScript interfaces
  parseJSON.ts            ← robust JSON extractor for AI responses
```
