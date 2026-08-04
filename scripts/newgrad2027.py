import re
import requests
from datetime import datetime, timezone

RAW_URL = "https://raw.githubusercontent.com/vanshb03/New-Grad-2027/dev/README.md"

TITLE_KEYWORDS = [
    "software engineer", "swe", "software developer",
    "forward deployed", "solutions engineer", "backend", "frontend",
    "full stack", "full-stack", "machine learning engineer", "ml engineer",
]

CLOSED_MARKER = "🔒"
MIN_DATE_POSTED = "2026-07-24"

def fetch_markdown():
    r = requests.get(RAW_URL, timeout=30)
    r.raise_for_status()
    return r.text

def extract_apply_link(cell):
    match = re.search(r'href="(https?://[^"]+)"', cell)
    return match.group(1) if match else None

def clean_company_name(cell):
    cell = re.sub(r"<[^>]+>", "", cell)
    return cell.replace("**", "").strip()

def clean_location(cell):
    cell = re.sub(r"\*\*\d+\s+locations?\*\*", "", cell)          # drop "**12 locations**" prefix
    cell = re.sub(r"</?br\s*/?>", ", ", cell, flags=re.IGNORECASE)  # <br>, </br>, <br/> -> ", "
    cell = re.sub(r"<[^>]+>", "", cell)                            # strip any other stray html
    cell = cell.replace("**", "")
    cell = re.sub(r"\s*,\s*", ", ", cell)
    return cell.strip(", ").strip()

def title_matches(title):
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)

def is_closed(role_cell):
    return CLOSED_MARKER in role_cell

def clean_title(role_cell):
    title = re.sub(r"[🛂🇺🇸🔒]", "", role_cell)
    return title.replace("**", "").strip()

def parse_date_posted(date_str):
    date_str = date_str.strip()
    today = datetime.now(timezone.utc).date()
    try:
        parsed = datetime.strptime(date_str, "%b %d").replace(year=today.year).date()
    except ValueError:
        return date_str  # fallback: keep raw value if format is unexpected

    if parsed > today:
        parsed = parsed.replace(year=today.year - 1)
    return parsed.strftime("%Y-%m-%d")

# parses the single big table in the README, using header row to determine columns
def parse_table(lines, header_index):
    header_cells = [c.strip() for c in lines[header_index].strip().strip("|").split("|")]
    col_index = {name.lower(): i for i, name in enumerate(header_cells)}

    jobs = []
    i = header_index + 2  # skip header row + the "----" divider row beneath it
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if len(cells) == len(header_cells):
            company_cell = cells[col_index["company"]]
            role_cell = cells[col_index["role"]]
            location_cell = cells[col_index["location"]]
            link_cell = cells[col_index["application/link"]]
            date_cell = cells[col_index["date posted"]]

            link = extract_apply_link(link_cell)
            company = clean_company_name(company_cell)
            title = clean_title(role_cell)
            date_posted = parse_date_posted(date_cell)

            if link and not is_closed(role_cell) and title_matches(title) and date_posted >= MIN_DATE_POSTED:
                jobs.append({
                    "id": link,
                    "company": company,
                    "title": title,
                    "location": clean_location(location_cell),
                    "link": link,
                    "date_posted": date_posted,
                    "source": "newgrad2027",
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
        if line.strip().startswith("|") and "Company" in line and "Role" in line:
            jobs, next_i = parse_table(lines, i)
            all_jobs.extend(jobs)
            i = next_i
        else:
            i += 1

    return all_jobs