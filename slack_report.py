# ------------- imports + setup --------------------------
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

import requests
import gspread
from google.oauth2.service_account import Credentials

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ---------------- access tracker -------------------------
def get_sheet():
    creds = Credentials.from_service_account_file("service_account.json", scopes=SHEETS_SCOPES)
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id).sheet1

# pulls every row and filters to jobs scraped today
def get_todays_jobs(sheet):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    records = sheet.get_all_records()
    todays = [r for r in records if r.get("date_scraped") == today]

    # sort by relevance score, highest first — falls back to 0 if
    # score is missing/blank so it doesn't crash on empty strings
    def score_key(r):
        try:
            return int(r.get("relevance_score", 0))
        except (ValueError, TypeError):
            return 0

    todays.sort(key=score_key, reverse=True)
    return todays

# ------------------- slack ----------------------------
def format_message(jobs):
    if not jobs:
        return "No new postings found today."

    lines = [f"*{len(jobs)} new postings today* :briefcase:\n"]
    for job in jobs:
        score = job.get("relevance_score", "?")
        reason = job.get("relevance_reason", "")
        lines.append(
            f"*{job['company']}* — {job['title']}\n"
            f"  {job['location']} | score: {score}/10 | {reason}\n"
            f"  <{job['link']}|Apply here>\n"
        )
    return "\n".join(lines)

def send_to_slack(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    r = requests.post(webhook_url, json={"text": message})
    r.raise_for_status()
    return r.status_code

if __name__ == "__main__":
    print("Connecting to Google Sheet...")
    sheet = get_sheet()

    print("Finding today's new postings...")
    jobs = get_todays_jobs(sheet)
    print(f"Found {len(jobs)} postings from today")

    print("Formatting and sending to Slack...")
    message = format_message(jobs)
    status = send_to_slack(message)
    print(f"Sent — Slack responded with status {status}")