import os
from dotenv import load_dotenv
load_dotenv()

import gspread
from google.oauth2.service_account import Credentials
from supabase import create_client

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
BATCH_SIZE = 500

def get_sheets():
    creds = Credentials.from_service_account_file("service_account.json", scopes=SHEETS_SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID"))
    return spreadsheet.worksheet("job_postings"), spreadsheet.worksheet("status_history")

def clean_job_row(row):
    score = row.get("relevance_score")
    row["relevance_score"] = int(score) if str(score).strip().isdigit() else None
    return row

def clean_history_row(row):
    # Sheets timestamps are "YYYY-MM-DD HH:MM:SS" UTC; Postgres wants ISO 8601
    row["timestamp"] = row["timestamp"].replace(" ", "T") + "Z"
    return row

def migrate():
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    jobs_sheet, history_sheet = get_sheets()

    print("Reading job postings...")
    jobs = [clean_job_row(r) for r in jobs_sheet.get_all_records()]
    print(f"  {len(jobs)} rows")

    print("Reading status history...")
    events = [clean_history_row(r) for r in history_sheet.get_all_records()]
    print(f"  {len(events)} rows")

    print("Inserting job postings...")
    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i:i + BATCH_SIZE]
        supabase.table("job_postings").insert(batch).execute()
        print(f"  inserted {i + len(batch)}/{len(jobs)}")

    print("Inserting status history...")
    for i in range(0, len(events), BATCH_SIZE):
        batch = events[i:i + BATCH_SIZE]
        supabase.table("status_history").insert(batch).execute()
        print(f"  inserted {i + len(batch)}/{len(events)}")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()