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

def mark_status(job_id, new_status):
    """
    Finds the row matching job_id and updates its status column.
    Returns True if a matching row was found and updated, False otherwise
    — the caller (the agent) needs to know if the update actually happened,
    since a wrong/stale job_id shouldn't fail silently.
    """
    sheet = get_sheet()
    records = sheet.get_all_records()
    header = sheet.row_values(1)
    status_col = header.index("status") + 1

    for i, row in enumerate(records, start=2):  # row 1 is the header
        if row.get("id") == job_id:
            sheet.update_cell(i, status_col, new_status)
            return True
    return False