# Job Search Agent

An automated pipeline that collects new-grad Software Engineering / Forward Deployed Engineer job postings, filters and scores them against personal preferences using Claude, tracks them in Google Sheets, and provides a conversational agent to search and manage application status — with a daily Slack digest of new postings.

Built as a personal tool to reduce the manual overhead of a new-grad job search (target: Summer/Fall 2027 start), and as a hands-on project in building agentic tools with the Claude API, and full-stack web development.

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
                         │  FastAPI backend (api/)                    │
                         │  Wraps agent.py + sheet_tools.py as         │
                         │  REST endpoints: /jobs, /jobs/{id}/status,  │
                         │  /chat, /metrics, /history                  │
                         └──────────────────────────────────────────┘
                                            │
                                            v
                         ┌──────────────────────────────────────────┐
                         │  Next.js + Tailwind frontend (frontend/)   │
                         │  Metrics tiles, weekly status history      │
                         │  chart, chat interface, top 10 unapplied    │
                         │  jobs — calls the FastAPI backend            │
                         └──────────────────────────────────────────┘

         Collection/classification/Slack digest are run daily,
         automatically, via GitHub Actions (.github/workflows/daily.yml).
         The frontend and backend are deployed separately (see below).
```

## What it does

1. **Collects** active new-grad SWE postings from curated GitHub repos (currently `speedyapply/2027-SWE-College-Jobs`; `SimplifyJobs/New-Grad-Positions` is supported but disabled until it adds 2027 postings)
2. **Filters** by title keywords (software engineer, backend, frontend, forward deployed, etc.) and active/visible status
3. **Deduplicates** against what's already been collected, so re-running never creates duplicate rows
4. **Classifies** each new posting with the Claude API against personal preferences — location tiers, and hard-excludes for defense/government contractors and companies associated with ICE/surveillance work (both via an explicit blocklist for known companies and a prompt-based fallback for others)
5. **Stores** everything in a Google Sheet — id, company, title, location, link, source, date posted, date scraped, status, relevance score, relevance reason — plus a `status_history` tab logging every status transition as an event
6. **Reports** newly found postings to Slack once a day, sorted by relevance score
7. **Runs automatically** every day via a GitHub Actions scheduled workflow — no manual steps required for collection
8. **Serves a web dashboard** (Next.js + Tailwind frontend, FastAPI backend) showing status metrics, a weekly status history chart, the top 10 unapplied jobs, and a conversational agent (Claude tool-use) to search postings and update application status directly through chat

## File structure

```
job-search-agent/
├── collect_github.py          # Main collector: fetch, filter, dedup, classify, write to sheet
├── sheet_tools.py              # Shared Google Sheets read/write logic (used by agent + collector + API)
├── slack_report.py             # Formats and sends today's new postings to Slack
├── reclassify.py               # One-off batch re-classification of existing rows
├── agent.py                    # Claude tool-use agent: search_jobs / mark_status tools
├── sources/
│   ├── __init__.py
│   ├── simplifyjobs.py         # SimplifyJobs source (currently disabled — 2026 postings only)
│   └── speedyapply.py          # speedyapply 2027-SWE-College-Jobs source
├── api/                          # FastAPI backend (new) — wraps agent.py/sheet_tools.py as REST endpoints
│   ├── main.py                    # App entrypoint, route registration
│   └── routes/                    # /jobs, /jobs/{id}/status, /chat, /metrics, /history
├── frontend/                     # Next.js + Tailwind frontend (new)
│   ├── app/                       # Pages: dashboard, chat
│   └── components/                # Metrics tiles, status history chart, job list, chat panel
├── dashboard.py                # [legacy] Streamlit dashboard — being replaced by frontend/ + api/
├── .github/workflows/
│   └── daily.yml                # Scheduled automation (runs collector + Slack report daily)
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
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full service account JSON (used as a GitHub Actions secret; written to a local file at runtime in CI, and used by the FastAPI backend locally/in deployment) |

Locally, these live in `.env`. In GitHub Actions, they're stored as repository secrets and injected as environment variables in the workflow. The FastAPI backend will need the same variables set in its deployment environment (see below).

## Running locally

**Collector, classifier, Slack digest (unchanged):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

python collect_github.py      # fetch, filter, classify, save new postings
python slack_report.py        # send today's new postings to Slack
```

**Web dashboard (new direction — in progress):**

```powershell
# backend
cd api
pip install -r requirements.txt
uvicorn main:app --reload      # serves REST API for the frontend

# frontend (separate terminal)
cd frontend
npm install
npm run dev                    # Next.js dev server, calls the FastAPI backend
```

**Legacy Streamlit dashboard (being phased out):**

```powershell
streamlit run dashboard.py
```

## Automation

`.github/workflows/daily.yml` runs `collect_github.py` then `slack_report.py` automatically once a day (currently scheduled ~12pm Central, adjusted for UTC in the cron expression). Can also be triggered manually from the Actions tab in GitHub. This part of the pipeline is unaffected by the dashboard migration.

## The web app (new direction)

The dashboard is being rebuilt as a proper full-stack app instead of a single-script Streamlit app, for two reasons: Streamlit's full-script rerun model was causing slow (10-15s) reloads on every button click, and its CSS/layout customization was difficult to get right; and a Next.js + FastAPI stack is a stronger demonstration of full-stack skills for job applications.

**Backend (`api/`, FastAPI):** thin REST layer over the existing `agent.py` and `sheet_tools.py` logic — no business logic is being rewritten, just exposed over HTTP.

| Endpoint | Purpose |
|---|---|
| `GET /jobs` | List/filter saved postings (wraps `search_jobs`) |
| `PATCH /jobs/{id}/status` | Update a posting's status (wraps `mark_status`) |
| `POST /chat` | Send a message to the Claude tool-use agent (wraps `ask_agent`) |
| `GET /metrics` | Status counts for the metric tiles (wraps `get_status_counts`) |
| `GET /history` | Weekly status history for the chart (wraps `get_status_history_weekly`) |

**Frontend (`frontend/`, Next.js + Tailwind):** reimplements the same elements as the Streamlit dashboard — status count tiles, a weekly status history chart, a top-10-unapplied-jobs list with "Mark Applied" actions, and a chat interface for the agent — with real component-level updates instead of full-page reruns, and full CSS control via Tailwind.

**Planned deployment:** Next.js frontend on Vercel; FastAPI backend on Render, Railway, or Fly.io.

## Status / next steps

- [x] Multi-source collection with dedup
- [x] Personalized Claude classification
- [x] Google Sheets storage (including `status_history` event log)
- [x] Slack daily digest
- [x] Full automation via GitHub Actions
- [x] Conversational agent for search + status updates
- [x] "Mark applied" button in the dashboard
- [x] Dashboard metrics (status counts, weekly status history chart)
- [x] Streamlit dashboard as first working version
- [ ] **FastAPI backend wrapping agent.py/sheet_tools.py (in progress)**
- [ ] **Next.js + Tailwind frontend replacing the Streamlit dashboard (in progress)**
- [ ] Deploy backend (Render/Railway/Fly.io) and frontend (Vercel)
- [ ] Retire `dashboard.py` once the new frontend reaches feature parity
- [ ] Dealbreaker filtering in default dashboard view
- [ ] Additional sources (Greenhouse/Lever/Ashby direct pulls, Gmail parsing for LinkedIn/Handshake alerts)
- [ ] Re-enable SimplifyJobs once it adds 2027 postings
