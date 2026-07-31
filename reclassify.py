import os
import time
from dotenv import load_dotenv
load_dotenv()

import gspread
from google.oauth2.service_account import Credentials

from collect_github import classify_job, SHEETS_SCOPES  # reuse the existing function

def get_sheet():
    creds = Credentials.from_service_account_file("service_account.json", scopes=SHEETS_SCOPES)
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id).sheet1

if __name__ == "__main__":
    sheet = get_sheet()
    records = sheet.get_all_records()  # each dict also implicitly corresponds to a row

    print(f"Re-classifying {len(records)} existing postings...")

    for i, row in enumerate(records, start=2):  # row 1 is the header, data starts at row 2
        job = {"company": row["company"], "title": row["title"], "location": row["location"]}
        result = classify_job(job)

        # find the relevance_score and relevance_reason columns by header name
        header = sheet.row_values(1)
        score_col = header.index("relevance_score") + 1
        reason_col = header.index("relevance_reason") + 1

        sheet.update_cell(i, score_col, result.get("score", ""))
        sheet.update_cell(i, reason_col, result.get("reason", ""))

        print(f"  [{i-1}/{len(records)}] {row['company']} — score: {result.get('score')}")
        time.sleep(0.5)  # be polite to the Sheets API rate limit

    print("Done.")