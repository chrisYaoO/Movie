from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "movie-491021-a3b07c0b565a.json"
SPREADSHEET_ID = "19yDSkK0a_iOlcTlQ4MoD8w2RvZo0ieP-N3p_H2-NqFg"
RANGE_NAME = "Sheet1!A:D"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def append_test_row():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    service = build("sheets", "v4", credentials=creds)

    values = [
        ["test movie", "2024", "test director", "https://example.com"]
    ]

    body = {
        "values": values
    }

    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="RAW",
        body=body
    ).execute()

    print("写入成功")
    print(result)

if __name__ == "__main__":
    append_test_row()