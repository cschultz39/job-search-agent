import os
import json
from dotenv import load_dotenv
import requests

load_dotenv()

HEADERS = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
REPO = "SimplifyJobs/New-Grad-Positions"
JSON_PATH = ".github/scripts/listings.json"

def fetch_listings():
    url = f"https://api.github.com/repos/{REPO}/contents/{JSON_PATH}"
    r = requests.get(url, headers={**HEADERS, "Accept": "application/vnd.github.raw"})
    # throws an error if the request failed
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    print("Fetching listings.json...")
    data = fetch_listings()

    print(f"Type of data: {type(data)}")
    if isinstance(data, list):
        print(f"Number of listings: {len(data)}")
        print("\nFirst listing (raw structure):")
        print(json.dumps(data[0], indent=2))
    elif isinstance(data, dict):
        print("Top-level keys:", list(data.keys()))