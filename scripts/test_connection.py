import os
from dotenv import load_dotenv
from anthropic import Anthropic
import requests

load_dotenv()

# test 1: anthropic api
print("Testing Anthropic API...")
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=50,
    messages=[{"role": "user", "content": "Reply with just the word 'connected' if you receive this."}]
)
print("Anthropic response:", response.content[0].text)

# test 2: github api
print("\nTesting GitHub API...")
headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
r = requests.get("https://api.github.com/rate_limit", headers=headers)
print("GitHub rate limit remaining:", r.json()["rate"]["remaining"], "/", r.json()["rate"]["limit"])

# test 3: slack webhook
print("\nTesting Slack webhook...")
slack_url = os.getenv("SLACK_WEBHOOK_URL")
r = requests.post(slack_url, json={"text": "✅ Job search agent connected successfully."})
print("Slack status code:", r.status_code)