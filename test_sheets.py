import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheet():
    creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id).sheet1

if __name__ == "__main__":
    print("Connecting to Google Sheet...")
    sheet = get_sheet()

    print("Current header row:", sheet.row_values(1))

    print("Writing a test row...")
    sheet.append_row(["TestCo", "Test Engineer", "Remote", "https://example.com", "test", "2026-07-30", "2026-07-30", "not applied", ""])

    print("Done — check your sheet for a new 'TestCo' row.")