# Job Search Agent

An automated pipeline that collects new-grad Software Engineering / Forward Deployed Engineer job postings, filters and scores them against personal preferences using Claude, tracks them in Google Sheets, and provides a conversational agent (via Streamlit) to search and manage application status — with a daily Slack digest of new postings.

Built as a personal tool to reduce the manual overhead of a new-grad job search (target: Summer/Fall 2027 start), and as a hands-on project in building agentic tools with the Claude API.

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
                         │  Streamlit dashboard (dashboard.py)        │
                         │  Chat-based agent (agent.py) using         │
                         │  Claude tool-use to search/filter jobs      │
                         │  and update application status              │
                         └──────────────────────────────────────────┘

         Everything above is run daily, automatically, via
                    GitHub Actions (.github/workflows/daily.yml)
```

## What it does

1. **Collects** active new-grad SWE postings from curated GitHub repos (currently `speedyapply/2027-SWE-College-Jobs`; `SimplifyJobs/New-Grad-Positions` is supported but disabled until it adds 2027 postings)
2. **Filters** by title keywords (software engineer, backend, frontend, forward deployed, etc.) and active/visible status
3. **Deduplicates** against what's already been collected, so re-running never creates duplicate rows
4. **Classifies** each new posting with the Claude API against personal preferences — location tiers, and hard-excludes for defense/government contractors and companies associated with ICE/surveillance work (both via an explicit blocklist for known companies and a prompt-based fallback for others)
5. **Stores** everything in a Google Sheet — id, company, title, location, link, source, date posted, date scraped, status, relevance score, relevance reason
6. **Reports** newly found postings to Slack once a day, sorted by relevance score
7. **Runs automatically** every day via a GitHub Actions scheduled workflow — no manual steps required
8. **Provides a conversational agent** (Streamlit + Claude tool-use) to ask things like *"top 10 unapplied jobs by relevance score"* and to mark postings as applied/interviewing/etc. directly through chat

## File structure

```
job-search-agent/
├── collect_github.py          # Main collector: fetch, filter, dedup, classify, write to sheet
├── sheet_tools.py              # Shared Google Sheets read/write logic (used by agent + collector)
├── slack_report.py             # Formats and sends today's new postings to Slack
├── reclassify.py               # One-off batch re-classification of existing rows
├── agent.py                    # Claude tool-use agent: search_jobs / mark_status tools
├── dashboard.py                # Streamlit chat UI wrapping agent.py
├── sources/
│   ├── __init__.py
│   ├── simplifyjobs.py         # SimplifyJobs source (currently disabled — 2026 postings only)
│   └── speedyapply.py          # speedyapply 2027-SWE-College-Jobs source
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
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full service account JSON (used as a GitHub Actions secret; written to a local file at runtime in CI) |

Locally, these live in `.env`. In GitHub Actions, they're stored as repository secrets and injected as environment variables in the workflow.

## Running locally

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

python collect_github.py      # fetch, filter, classify, save new postings
python slack_report.py        # send today's new postings to Slack
streamlit run dashboard.py    # launch the chat-based agent dashboard
```

## Automation

`.github/workflows/daily.yml` runs `collect_github.py` then `slack_report.py` automatically once a day (currently scheduled ~12pm Central, adjusted for UTC in the cron expression). Can also be triggered manually from the Actions tab in GitHub.

## The agent (dashboard.py + agent.py)

Built using Claude's tool-use (function calling) API. Two tools are exposed to Claude:
- `search_jobs(status, min_score, company, limit)` — reads and filters the sheet
- `mark_status(job_id, new_status)` — updates a posting's status, constrained to a fixed set of valid values (`not applied`, `applied`, `interviewing`, `offer`, `rejected`, `withdrawn`) via both the tool schema's `enum` and backend validation

The Streamlit UI wraps this in a chat interface using `st.session_state` to persist conversation history across Streamlit's re-run-on-every-interaction model.

## Status / next steps

- [x] Multi-source collection with dedup
- [x] Personalized Claude classification
- [x] Google Sheets storage
- [x] Slack daily digest
- [x] Full automation via GitHub Actions
- [x] Conversational agent for search + status updates
- [ ] "Mark applied" button in the dashboard (in progress)
- [ ] Dashboard metrics (total saved / applied / interviewing counts)
- [ ] Dealbreaker filtering in default dashboard view
- [ ] Visual polish pass on the dashboard
- [ ] Additional sources (Greenhouse/Lever/Ashby direct pulls, Gmail parsing for LinkedIn/Handshake alerts)
- [ ] Re-enable SimplifyJobs once it adds 2027 postings
- [ ] Deployment (Streamlit Community Cloud) for a shareable link
