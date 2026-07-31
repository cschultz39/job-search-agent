import os
from dotenv import load_dotenv
import requests

load_dotenv()
HEADERS = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}

# Get the full file tree of the repo in one call
url = "https://api.github.com/repos/SimplifyJobs/New-Grad-Positions/git/trees/dev?recursive=1"
r = requests.get(url, headers=HEADERS)
r.raise_for_status()
tree = r.json()["tree"]

# Find anything that looks like a listings file
for item in tree:
    if "json" in item["path"].lower() and "listing" in item["path"].lower():
        print(item["path"])