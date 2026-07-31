# ------------ imports --------------------
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
import json
from anthropic import Anthropic

from sources import simplifyjobs

# ------------ setup ------------------------
load_dotenv()

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# --------------- relevance score via claude ----------------

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CLASSIFICATION_PROMPT = """You are helping a computer science student graduating May 2027 evaluate new-grad job postings for Forward Deployed Engineer (FDE) or Software Engineer (SWE) roles.

Given this posting:
Company: {company}
Title: {title}
Location: {location}

Respond with ONLY a JSON object, no other text, in this exact format:
{{"relevant": true or false, "score": 1-10, "reason": "one short sentence"}}

A posting is relevant if it's a genuine new-grad/entry-level SWE, backend, frontend, full-stack, ML engineer, or forward-deployed/solutions engineer role. Score higher for roles that closely match FDE or general SWE work. Score lower (but still relevant: true) for adjacent roles. Set relevant: false only if it's clearly not a software engineering role despite matching our keyword filter."""

def classify_job(job):
    prompt = CLASSIFICATION_PROMPT.format(
        company=job["company"], title=job["title"], location=job["location"]
    )
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()
    raw_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"  Could not parse classification for {job['company']}: {raw_text}")
        result = {"relevant": True, "score": 5, "reason": "classification failed, defaulted"}

# ----------------- add to tracker -------------------------

def get_sheet():
    creds = Credentials.from_service_account_file("service_account.json", scopes=SHEETS_SCOPES)
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id).sheet1

def get_existing_ids(sheet):
    records = sheet.get_all_records()
    return {row["id"] for row in records if row.get("id")}

def add_new_jobs(sheet, jobs, existing_ids):
    new_count = 0
    for job in jobs:
        if job["id"] in existing_ids:
            continue

        print(f"  Classifying: {job['company']} — {job['title']}")
        classification = classify_job(job)

        sheet.append_row([
            job["id"],
            job["company"],
            job["title"],
            job["location"],
            job["link"],
            job["date_posted"],
            datetime.now(timezone.utc).strftime("%Y-%m-%d"),  # date_scraped
            "not applied",  # status TBD
            classification.get("score", ""),
            classification.get("reason", ""),
        ])
        new_count += 1
    return new_count

if __name__ == "__main__":
    print("Fetching from sources...")
    jobs = simplifyjobs.get_jobs()
    print(f"{len(jobs)} postings match filters (simplifyjobs)")

    print("Connecting to Google Sheet...")
    sheet = get_sheet()

    print("Checking which ones are already saved...")
    existing_ids = get_existing_ids(sheet)
    print(f"{len(existing_ids)} already in the sheet")

    print("Adding new postings...")
    added = add_new_jobs(sheet, jobs, existing_ids)
    print(f"\nAdded {added} new posting(s) to the sheet.")