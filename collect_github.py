# ------------ imports --------------------
import os
import json
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
import requests
import gspread
from google.oauth2.service_account import Credentials

# ------------ setup ------------------------
load_dotenv()

HEADERS = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
RAW_URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"
RELEVANT_CATEGORIES = {"Software Engineering"}
TITLE_KEYWORDS = [
    "software engineer", "swe", "software developer",
    "forward deployed", "solutions engineer", "backend", "frontend",
    "full stack", "full-stack", "machine learning engineer", "ml engineer",
]

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ------------------ fetch from github ---------------------

def fetch_listings(max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(RAW_URL, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.json()
        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError) as e:
            print(f"Attempt {attempt} failed ({e.__class__.__name__}), retrying...")
            time.sleep(2)
    raise RuntimeError("Failed to fetch listings.json after multiple retries")

def title_matches(title):
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)

def filter_and_clean(raw_listings):
    jobs = []
    for entry in raw_listings:
        if not entry.get("active") or not entry.get("is_visible"):
            continue
        if entry.get("category") not in RELEVANT_CATEGORIES:
            continue
        if not title_matches(entry.get("title", "")):
            continue

        jobs.append({
            "id": entry["id"],
            "company": entry["company_name"],
            "title": entry["title"],
            "location": ", ".join(entry.get("locations", [])),
            "link": entry["url"],
            "category": entry["category"],
            "sponsorship": entry.get("sponsorship"),
            "date_posted": datetime.fromtimestamp(entry["date_posted"], tz=timezone.utc).strftime("%Y-%m-%d"),
        })

    jobs.sort(key=lambda j: j["date_posted"], reverse=True)
    return jobs


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
        sheet.append_row([
            job["id"],
            job["company"],
            job["title"],
            job["location"],
            job["link"],
            job["date_posted"],
            datetime.now(timezone.utc).strftime("%Y-%m-%d"),  # date_scraped
            "not applied",  # status — you'll update this manually as you go
            "",  # notes
        ])
        new_count += 1
    return new_count

if __name__ == "__main__":
    print("Fetching listings.json...")
    raw = fetch_listings()

    print("Filtering to active, relevant postings...")
    jobs = filter_and_clean(raw)

    print("Connecting to Google Sheet...")
    sheet = get_sheet()

    print("Checking which ones are already saved...")
    existing_ids = get_existing_ids(sheet)
    print(f"{len(existing_ids)} already in the sheet")

    print("Adding new postings...")
    added = add_new_jobs(sheet, jobs, existing_ids)
    print(f"\nAdded {added} new posting(s) to the sheet.")