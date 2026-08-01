import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

import gspread
from google.oauth2.service_account import Credentials

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

STATUS_HISTORY_HEADER = ["job_id", "old_status", "new_status", "timestamp"]
STATUS_OPTIONS = [
    "not applied", "applied", "oa", "behavioral interview", "technical interview", "offer", "rejected", "withdrawn",
]

# in-memory cache of id -> row number
_id_to_row = {}

def get_sheet():
    if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
        with open("service_account.json", "w") as f:
            f.write(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    creds = Credentials.from_service_account_file("service_account.json", scopes=SHEETS_SCOPES)
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id).sheet1

def get_spreadsheet():
    if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
        with open("service_account.json", "w") as f:
            f.write(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    creds = Credentials.from_service_account_file("service_account.json", scopes=SHEETS_SCOPES)
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id)

def get_status_history_sheet():
    spreadsheet = get_spreadsheet()
    try:
        return spreadsheet.worksheet("status_history")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="status_history", rows=1000, cols=len(STATUS_HISTORY_HEADER))
        ws.append_row(STATUS_HISTORY_HEADER)
        return ws

def search_jobs(status=None, min_score=None, company=None, limit=10):
    sheet = get_sheet()
    records = sheet.get_all_records()

    def score_of(r):
        try:
            return int(r.get("relevance_score", 0))
        except (ValueError, TypeError):
            return 0

    results = records
    if status is not None:
        results = [r for r in results if r.get("status", "").lower() == status.lower()]
    if min_score is not None:
        results = [r for r in results if score_of(r) >= min_score]
    if company is not None:
        results = [r for r in results if company.lower() in r.get("company", "").lower()]

    results.sort(key=score_of, reverse=True)
    return results[:limit]

def get_status_history_weekly():
    history_sheet = get_status_history_sheet()
    events = history_sheet.get_all_records()

    if not events:
        return []
    
    def parse_ts(ts_str):
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    
    events = sorted(events, key=lambda e: parse_ts(e["timestamp"]))

    job_status = {}
    first_week_start = parse_ts(events[0]["timestamp"])
    first_week_start -= timedelta(days=first_week_start.weekday())
    current_week_start = datetime.now(timezone.utc)
    current_week_start -= timedelta(days=current_week_start.weekday())

    weekly_snapshots = []
    week_start = first_week_start
    event_idx = 0
    while week_start <= current_week_start:
        week_end = week_start + timedelta(days=7)
        while event_idx < len(events) and parse_ts(events[event_idx]["timestamp"]) < week_end:
            e = events[event_idx]
            job_status[e["job_id"]] = e["new_status"]
            event_idx += 1

        snapshot = {status: 0 for status in STATUS_OPTIONS}
        for status in job_status.values():
            if status in snapshot:
                snapshot[status] += 1
        weekly_snapshots.append({"week_of": week_start.strftime("%Y-%m-%d"), **snapshot})

        week_start = week_end

    return weekly_snapshots

def get_status_counts():
    sheet = get_sheet()
    records = sheet.get_all_records()

    counts = {status: 0 for status in STATUS_OPTIONS}
    for r in records:
        status = r.get("status", "")
        if status in counts:
            counts[status] += 1
    return counts

def _refresh_id_cache(sheet, id_col):
    global _id_to_row
    values = sheet.col_values(id_col)  # index 0 is the header row
    _id_to_row = {
        job_id: row_num
        for row_num, job_id in enumerate(values, start=1)
        if row_num > 1 and job_id
    }

def mark_status(job_id, new_status):
    if new_status not in STATUS_OPTIONS:
        return {"success": False, "error": f"'{new_status}' is not a valid status. Must be one of: {', '.join(STATUS_OPTIONS)}"}

    sheet = get_sheet()
    header = sheet.row_values(1)
    id_col = header.index("id") + 1
    status_col = header.index("status") + 1

    if not _id_to_row:
        _refresh_id_cache(sheet, id_col)

    row = _id_to_row.get(job_id)

    # cache miss = rebuild once before concluding it doesn't exist
    if row is None:
        _refresh_id_cache(sheet, id_col)
        row = _id_to_row.get(job_id)

    if row is None:
        return {"success": False, "error": "job_id not found"}
    
    old_status = sheet.cell(row, status_col).value
    sheet.update_cell(row, status_col, new_status)

    try:
        history_sheet = get_status_history_sheet()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        history_sheet.append_row([job_id, old_status, new_status, timestamp])
    except Exception as e:
        print(f"Warning: status update succeeded but history logging failed: {e}")

    return {"success": True}