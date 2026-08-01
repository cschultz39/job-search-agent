# ------------ imports --------------------
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import json
from anthropic import Anthropic

# ------------ setup ------------------------
load_dotenv()

from sources import speedyapply
from sheet_tools import get_status_history_sheet, get_sheet

# --------------- relevance score via claude ----------------
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CLASSIFICATION_PROMPT = """You are helping a computer science student graduating May 2027 evaluate new-grad job postings for Forward Deployed Engineer (FDE) or Software Engineer (SWE) roles.

Given this posting:
Company: {company}
Title: {title}
Location: {location}

The candidate's preferences:
- Location, in order of preference: (1) Chicago, (2) Chicagoland Area, (3) Big Cities in the Midwest, (4) Portland/Washington, (5) anywhere in the USA as a lower-priority fallback
- No preference on company type/size (big tech, startup, and quant/finance are all fine)
- Hard dealbreakers: defense contractors and government-sector roles (e.g. Raytheon, Boeing, Northrop Grumman, Lockheed, GDIT, Leidos, CACI, Booz Allen, or any role requiring a security clearance) — these should always be marked not relevant regardless of anything else about the posting

Respond with ONLY a JSON object, no other text, in this exact format:
{{"relevant": true or false, "score": 1-10, "reason": "one short sentence"}}

Scoring guidance:
- Set relevant: false and score: 1 for anything matching a dealbreaker above, regardless of how good the role otherwise looks
- For non-dealbreaker postings, score higher for roles that closely match FDE or general SWE work AND match a higher-priority location tier
- A strong SWE/FDE role in a lower-priority location should still score reasonably (5-7), not be penalized as heavily as an actual dealbreaker
- Score lower (5-7) but still relevant: true for adjacent roles or acceptable-but-not-ideal locations
- Only use relevant: false for dealbreaker matches or roles that clearly aren't software engineering work despite matching our keyword filter"""

BLOCKED_COMPANIES = {
    "palantir",
    "flock safety",
    "at&t",
    "deloitte",
    "motorola solutions",
    "l3 harris",
    "fedex",
    "comcast",
    "charter communications",
    "clearview ai",
    "axon",
    "geolitica",
    "lexisnexis",
    "dji",
    "digital receiver technology",
    "fog data science",
}

def is_blocked_company(company_name):
    return company_name.strip().lower() in BLOCKED_COMPANIES

def classify_job(job):
    prompt = CLASSIFICATION_PROMPT.format(
        company=job["company"], title=job["title"], location=job["location"]
    )
    fallback = {"relevant": True, "score": 5, "reason": "classification failed, defaulted"}

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = response.content[0].text.strip()
        raw_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw_text)

        # guard against valid-JSON-but-wrong-shape responses
        if not isinstance(result, dict) or "score" not in result:
            print(f"  Unexpected classification shape for {job['company']}: {raw_text}")
            return fallback

        return result
    
    except Exception as e:
        # catches JSON errors AND API-level issues
        print(f"  Classification error for {job['company']}: {e}")
        return fallback

# ----------------- add to tracker -------------------------
def get_existing_ids(sheet):
    records = sheet.get_all_records()
    return {row["id"] for row in records if row.get("id")}

def add_new_jobs(sheet, jobs, existing_ids):
    new_count = 0
    for job in jobs:
        if job["id"] in existing_ids:
            continue

        if is_blocked_company(job["company"]):
            print(f"  Blocked company, skipping classification: {job['company']}")
            classification = {"relevant": False, "score": 1, "reason": "blocked company (ICE/surveillance)"}
        else:
            print(f"  Classifying: {job['company']} — {job['title']}")
            classification = classify_job(job)

        sheet.append_row([
            job["id"],
            job["company"],
            job["title"],
            job["location"],
            job["link"],
            job["source"],
            job["date_posted"],
            datetime.now(timezone.utc).strftime("%Y-%m-%d"),  # date_scraped
            "not applied",  # status TBD
            classification.get("score", ""),
            classification.get("reason", ""),
        ])

        try:
            history_sheet = get_status_history_sheet()
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            history_sheet.append_row([job["id"], "n/a", "not applied", timestamp])
        except Exception as e:
            print(f"  Warning: job added but history logging failed: {e}")

        new_count += 1
    return new_count

if __name__ == "__main__":
    print("Fetching from sources...")
    jobs = speedyapply.get_jobs()
    print(f"{len(jobs)} postings match filters")

    print("Connecting to Google Sheet...")
    sheet = get_sheet()

    print("Checking which ones are already saved...")
    existing_ids = get_existing_ids(sheet)
    print(f"{len(existing_ids)} already in the sheet")

    print("Adding new postings...")
    added = add_new_jobs(sheet, jobs, existing_ids)
    print(f"\nAdded {added} new posting(s) to the sheet.")