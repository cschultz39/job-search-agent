# ------------- imports + setup --------------------------
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

from sheet_tools import get_sheet, get_status_history_sheet

# ------------- backfill logic ----------------------------
def get_already_logged_job_ids(history_sheet):
    records = history_sheet.get_all_records()
    return {r["job_id"] for r in records if r.get("job_id")}

def backfill(sheet, history_sheet):
    records = sheet.get_all_records()
    already_logged = get_already_logged_job_ids(history_sheet)

    rows_to_add = []
    skipped = 0
    for row in records:
        job_id = row.get("id")
        date_scraped = row.get("date_scraped")

        if not job_id or job_id in already_logged:
            skipped += 1
            continue

        if not date_scraped:
            print(f"  Skipping {job_id} — no date_scraped value")
            skipped += 1
            continue

        timestamp = f"{date_scraped} 00:00:00"
        rows_to_add.append([job_id, "n/a", "not applied", timestamp])

    if rows_to_add:
        # single batched write instead of one API call per row —
        # avoids the Sheets API's per-minute write quota
        history_sheet.append_rows(rows_to_add)

    return len(rows_to_add), skipped

if __name__ == "__main__":
    print("Connecting to Google Sheet...")
    sheet = get_sheet()
    history_sheet = get_status_history_sheet()

    print("Backfilling status_history from date_scraped...")
    backfilled, skipped = backfill(sheet, history_sheet)

    print(f"\nBackfilled {backfilled} job(s).")
    print(f"Skipped {skipped} job(s) (already logged or missing date_scraped).")