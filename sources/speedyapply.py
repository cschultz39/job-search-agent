import re
import requests
from datetime import datetime, timedelta, timezone

RAW_URL = "https://raw.githubusercontent.com/speedyapply/2027-SWE-College-Jobs/main/NEW_GRAD_USA.md"

TITLE_KEYWORDS = [
    "software engineer", "swe", "software developer",
    "forward deployed", "solutions engineer", "backend", "frontend",
    "full stack", "full-stack", "machine learning engineer", "ml engineer",
]

def fetch_markdown():
    r = requests.get(RAW_URL, timeout=30)
    r.raise_for_status()
    return r.text

# apply cell has two urls, need to grab the second one
def extract_apply_link(cell):
    match = re.search(r'href="(https?://[^"]+)"', cell)
    return match.group(1) if match else None

def clean_company_name(cell):
    return re.sub(r"<[^>]+>", "", cell).strip()

def title_matches(title):
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)

# converts a relative age like '7d' into an actual date string
def age_to_date(age_str):
    match = re.match(r"(\d+)d", age_str.strip())
    if not match:
        return age_str  # fallback: keep the raw value if it doesn't match "Xd"

    days_ago = int(match.group(1))
    posted_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return posted_date.strftime("%Y-%m-%d")

# parses one markdown table, using header row to determine columns
def parse_table(lines, header_index):
    header_cells = [c.strip() for c in lines[header_index].strip().strip("|").split("|")]
    col_index = {name.lower(): i for i, name in enumerate(header_cells)}

    jobs = []
    i = header_index + 2  # skip header row + the "----" divider row beneath it
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if len(cells) == len(header_cells):
            company_cell = cells[col_index["company"]]
            title = cells[col_index["position"]]
            location = cells[col_index["location"]]
            posting_cell = cells[col_index["posting"]]
            age = cells[col_index["age"]]

            link = extract_apply_link(posting_cell)
            company = clean_company_name(company_cell)

        if link and title_matches(title):
                jobs.append({
                    "id": link,
                    "company": company,
                    "title": title,
                    "location": location,
                    "link": link,
                    "date_posted": age_to_date(age),
                    "source": "speedyapply",
                })
        i += 1
    return jobs, i

def get_jobs():
    text = fetch_markdown()
    lines = text.split("\n")

    all_jobs = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and "Company" in line and "Position" in line:
            jobs, next_i = parse_table(lines, i)
            all_jobs.extend(jobs)
            i = next_i
        else:
            i += 1

    return all_jobs