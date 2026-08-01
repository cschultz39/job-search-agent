import os
from dotenv import load_dotenv
load_dotenv()

import gspread
from google.oauth2.service_account import Credentials

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheet():
    if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
        with open("service_account.json", "w") as f:
            f.write(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    creds = Credentials.from_service_account_file("service_account.json", scopes=SHEETS_SCOPES)
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id).sheet1

def search_jobs(status=None, min_score=None, company=None, limit=10):
    """
    Reads all rows, applies whatever filters were provided, sorts by
    relevance score (highest first), and returns up to `limit` results.
    Filters are all optional — pass only what you need.
    """
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


STATUS_OPTIONS = [
    "not applied", "applied", "oa", "behavioral interview", "technical interview", "offer", "rejected", "withdrawn",
]

# in-memory cache of id -> row number
_id_to_row = {}

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

    sheet.update_cell(row, status_col, new_status)
    return {"success": True}