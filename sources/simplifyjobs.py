import os
import time
from datetime import datetime, timezone
import requests

GITHUB_HEADERS = {"Authorization": f"token {os.getenv('GH_TOKEN_PAT')}"}
RAW_URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"
RELEVANT_CATEGORIES = {"Software Engineering"}
TITLE_KEYWORDS = [
    "software engineer", "swe", "software developer",
    "forward deployed", "solutions engineer", "backend", "frontend",
    "full stack", "full-stack", "machine learning engineer", "ml engineer",
]

def fetch_listings(max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(RAW_URL, headers=GITHUB_HEADERS, timeout=30)
            r.raise_for_status()
            return r.json()
        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError) as e:
            print(f"Attempt {attempt} failed ({e.__class__.__name__}), retrying...")
            time.sleep(2)
    raise RuntimeError("Failed to fetch listings.json after multiple retries")

def title_matches(title):
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)

def get_jobs():
    raw = fetch_listings()
    jobs = []
    for entry in raw:
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
            "date_posted": datetime.fromtimestamp(entry["date_posted"], tz=timezone.utc).strftime("%Y-%m-%d"),
            "source": "simplifyjobs",
        })
    return jobs