# Job Search Agent

An automated pipeline that collects new-grad Software Engineering / Forward Deployed Engineer job postings, filters and scores them against personal preferences using Claude, tracks them in Google Sheets, and provides a Next.js dashboard (backed by a FastAPI service) to browse postings and manage application status — with a daily Slack digest of new postings.

Built as a personal tool to reduce the manual overhead of a new-grad job search (target: Summer/Fall 2027 start), and as a hands-on project in building agentic tools with the Claude API and a full-stack web app.

## Architecture overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Data sources    │ --> │  Collector        │ --> │  Google Sheet    │
│  (GitHub repos)  │     │  (collect_github  │     │  (single source  │
│                  │     │  .py)             │     │  of truth)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                  │                          │
                                  v                          v
                         ┌──────────────────┐     ┌─────────────────┐
                         │  Claude API        │     │  Slack digest    │
                         │  classification    │     │  (slack_report   │
                         │  (relevance score) │     │  .py)            │
                         └──────────────────┘     └─────────────────┘

                         ┌──────────────────────────────────────────┐
                         │  FastAPI backend                           │
                         │  Wraps agent.py / sheet_tools.py logic      │
                         │  via /jobs, /jobs/status, /metrics,        │
                         │  /history, /chat endpoints                  │
                         └──────────────────────────────────────────┘
                                          │
                                          v
                         ┌──────────────────────────────────────────┐
                         │  Next.js + Tailwind dashboard               │
                         │  Metrics tiles, status-over-time chart,     │
                         │  unapplied jobs list — pixelated UI          │
                         │  in a strawberry matcha color palette        │
                         └──────────────────────────────────────────┘

         Everything in the collection pipeline is run daily,
         automatically, via GitHub Actions (.github/workflows/daily.yml)
```

**Note:** the dashboard was originally built in Streamlit (`dashboard.py` + `agent.py`'s chat-based tool-use agent). It has since been migrated to a Next.js + Tailwind frontend with a FastAPI backend, due to Streamlit's CSS/layout limitations and slow (10-15s) full-script reruns on every interaction. `dashboard.py` and `agent.py` are retained for reference but are no longer the active UI layer — see "Status / next steps" below for the plan to port the chat feature into the new stack.

## What it does

1. **Collects** active new-grad SWE postings from curated GitHub repos (currently `speedyapply/2027-SWE-College-Jobs`; `SimplifyJobs/New-Grad-Positions` is supported but disabled until it adds 2027 postings)
2. **Filters** by title keywords (software engineer, backend, frontend, forward deployed, etc.) and active/visible status
3. **Deduplicates** against what's already been collected, so re-running never creates duplicate rows
4. **Classifies** each new posting with the Claude API against personal preferences — location tiers, and hard-excludes for defense/government contractors and companies associated with ICE/surveillance work (both via an explicit blocklist for known companies and a prompt-based fallback for others)
5. **Stores** everything in a Google Sheet — id, company, title, location, link, source, date posted, date scraped, status, relevance score, relevance reason — plus a `status_history` tab logging every status transition as an event (job_id, old_status, new_status, timestamp)
6. **Reports** newly found postings to Slack once a day, sorted by relevance score
7. **Runs automatically** every day via a GitHub Actions scheduled workflow — no manual steps required
8. **Serves a dashboard** (Next.js frontend + FastAPI backend) showing status count tiles, a weekly status-history line chart (one line per status, color-matched to its tile), and the top 10 unapplied jobs with one-click "mark applied"

## File structure

```
job-search-agent/
├── collect_github.py          # Main collector: fetch, filter, dedup, classify, write to sheet
├── sheet_tools.py              # Shared Google Sheets read/write logic (used by API + collector)
├── slack_report.py             # Formats and sends today's new postings to Slack
├── reclassify.py               # One-off batch re-classification of existing rows
├── agent.py                    # Claude tool-use agent: search_jobs / mark_status tools (currently unused by the active UI — see note above)
├── dashboard.py                # Legacy Streamlit chat UI (superseded — see note above)
├── sources/
│   ├── __init__.py
│   ├── simplifyjobs.py         # SimplifyJobs source (currently disabled — 2026 postings only)
│   └── speedyapply.py          # speedyapply 2027-SWE-College-Jobs source
├── api/                         # FastAPI backend
│   └── main.py                  # /jobs, /jobs/status, /metrics, /history, /chat endpoints
├── frontend/                    # Next.js + Tailwind dashboard
│   ├── app/
│   │   ├── layout.tsx            # Root layout — loads Pixelify Sans + Press Start 2P fonts
│   │   ├── page.tsx              # Main dashboard page
│   │   └── globals.css           # Strawberry matcha color tokens, pixel-art tile/card styles
│   ├── components/
│   │   ├── MetricsTiles.tsx      # Status count tiles, colors sourced from lib/statusColors.ts
│   │   ├── StatusChart.tsx       # Weekly status-history chart (Recharts), one line per status
│   │   └── UnappliedJobs.tsx     # Scrollable unapplied jobs list with Apply/Mark Applied buttons
│   └── lib/
│       ├── api.ts                # Fetch wrappers for the FastAPI backend
│       └── statusColors.ts       # Single source of truth for status -> color/label mapping
├── .github/workflows/
│   └── daily.yml                 # Scheduled automation (runs collector + Slack report daily)
├── requirements.txt
├── .env                          # Local secrets (not committed)
├── service_account.json          # Google service account credentials (not committed)
└── .gitignore
```

## Data sources

| Source | Status | Notes |
|---|---|---|
| `speedyapply/2027-SWE-College-Jobs` | Active | Markdown tables (HTML-formatted cells), parsed via `sources/speedyapply.py` |
| `SimplifyJobs/New-Grad-Positions` | Disabled | Clean JSON backing (`listings.json`), but currently only has 2026 grad postings — re-enable once 2027 roles are added |

## Classification logic

Each new posting is sent to the Claude API with the candidate's preferences embedded in the prompt:
- **Location**, ranked: Chicago > Chicagoland Area > Big Cities in the Midwest > Portland/Washington > anywhere in the USA
- **No preference** on company type/size (big tech, startup, quant/finance all acceptable)
- **Hard dealbreakers** (always scored 1, marked not relevant):
  - Defense contractors / government-sector roles / clearance-required roles
  - Companies associated with ICE, immigration enforcement, or public/mass surveillance (checked first against an explicit blocklist for efficiency and reliability, with the Claude prompt as a fallback for companies not yet on the list)

Dealbreaker postings are currently still written to the sheet (visible, scored low) rather than excluded outright, so classification accuracy can be sanity-checked. A future dashboard update should filter these out of default views.

## Environment variables / secrets

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API access (classification + agent) |
| `GH_TOKEN_PAT` | GitHub API token (higher rate limits; named to avoid GitHub Actions' reserved `GITHUB_*` prefix) |
| `SLACK_WEBHOOK_URL` | Incoming webhook for the daily Slack digest |
| `GOOGLE_SHEET_ID` | Target Google Sheet ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full service account JSON (used as a GitHub Actions secret; written to a local file at runtime in CI) |
| `NEXT_PUBLIC_API_URL` | Base URL the frontend uses to reach the FastAPI backend |

Locally, the Python-side variables live in `.env`. In GitHub Actions, they're stored as repository secrets and injected as environment variables in the workflow.

## Running locally

```powershell
# Python side (collector, Slack report, FastAPI backend)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

python collect_github.py      # fetch, filter, classify, save new postings
python slack_report.py        # send today's new postings to Slack
uvicorn api.main:app --reload # launch the FastAPI backend

# Frontend
cd frontend
npm install
npm run dev                   # launch the Next.js dashboard
```

## Automation

`.github/workflows/daily.yml` runs `collect_github.py` then `slack_report.py` automatically once a day (currently scheduled ~12pm Central, adjusted for UTC in the cron expression). Can also be triggered manually from the Actions tab in GitHub.

## The dashboard (Next.js + FastAPI)

The FastAPI backend wraps the existing `sheet_tools.py` logic behind REST endpoints:
- `GET /jobs` — search/filter postings (`status`, `min_score`, `company`, `limit`), backed by `search_jobs()`
- `PATCH /jobs/status` — update a posting's status (`job_id`, `new_status`), backed by `mark_status()`, validated against the same fixed status set used throughout the sheet
- `GET /metrics` — status counts, backed by `get_status_counts()`
- `GET /history` — weekly status-history snapshots, backed by `get_status_history_weekly()`
- `/chat` — reserved for the conversational agent (not yet wired up in the new stack — see "Status / next steps")

The Next.js frontend renders three main pieces, all sharing a single `lib/statusColors.ts` mapping so colors, labels, and status order can never drift out of sync across components:
- **Metrics tiles** (`MetricsTiles.tsx`) — one tile per status, full-width row across the top
- **Status-over-time chart** (`StatusChart.tsx`) — Recharts line chart, one step-line per status, each colored to match its tile, with a custom tooltip that shows only the hovered status (or a small cluster of statuses within ~10 counts of each other, to handle overlapping zero-value dots)
- **Unapplied jobs list** (`UnappliedJobs.tsx`) — scrollable card matching the chart's height, each entry showing company/title/location/score with "Apply here" and "Mark applied" buttons

The UI uses a pixel-art aesthetic (Press Start 2P for headers/tile numbers/buttons, Pixelify Sans for body text, chunky offset drop-shadow borders instead of soft shadows) in a strawberry-matcha color palette — matcha greens for early/neutral statuses, strawberry pinks for interview stages, muted desaturated tones for rejected/withdrawn.

## Status / next steps

- [x] Multi-source collection with dedup
- [x] Personalized Claude classification
- [x] Google Sheets storage
- [x] Slack daily digest
- [x] Full automation via GitHub Actions
- [x] Migrate dashboard from Streamlit to Next.js + FastAPI
- [x] Metrics tiles, status-history chart, unapplied jobs list with mark-applied
- [x] Pixelated strawberry-matcha visual redesign
- [ ] **Floating chat widget** — port the `agent.py` tool-use agent (search_jobs / mark_status) into a chat interface on the Next.js dashboard, wired through the FastAPI `/chat` endpoint, styled to match the pixel-art theme
- [ ] Dealbreaker filtering in default dashboard view
- [ ] Additional sources (Greenhouse/Lever/Ashby direct pulls, Gmail parsing for LinkedIn/Handshake alerts)
- [ ] Re-enable SimplifyJobs once it adds 2027 postings
- [ ] Deployment — Next.js on Vercel, FastAPI on Render/Railway/Fly.io