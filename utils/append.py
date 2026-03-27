import json
import os

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SERVICE_ACCOUNT_FILE = os.path.join(
    BASE_DIR, "configs", "movie-491021-a3b07c0b565a.json"
)
DEFAULT_SPREADSHEET_IDS_FILE = os.path.join(BASE_DIR, "configs", "ids.json")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def load_service_account_credentials():
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        service_account_info = json.loads(service_account_json)
        return Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES,
        )

    service_account_file = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_FILE",
        DEFAULT_SERVICE_ACCOUNT_FILE,
    )
    return Credentials.from_service_account_file(service_account_file, scopes=SCOPES)


def read_id(name):
    spreadsheet_ids_json = os.getenv("SPREADSHEET_IDS_JSON")
    if spreadsheet_ids_json:
        data = json.loads(spreadsheet_ids_json)
    else:
        with open(DEFAULT_SPREADSHEET_IDS_FILE, encoding="utf-8") as file:
            data = json.load(file)
    return data[name]


def make_cell(value):
    if isinstance(value, (int, float)):
        return {"userEnteredValue": {"numberValue": value}}
    return {"userEnteredValue": {"stringValue": str(value)}}


def append_row(movie_info, status):
    creds = load_service_account_credentials()

    service = build("sheets", "v4", credentials=creds)
    res = service.spreadsheets().get(spreadsheetId=read_id(status)).execute()
    target_sheet_name = movie_info["sheetname"]
    target_sheet = None

    for sheet in res["sheets"]:
        if sheet.get("properties", {}).get("title") == target_sheet_name:
            target_sheet = sheet
            break

    if target_sheet is None:
        raise ValueError(f'Sheet "{target_sheet_name}" not found.')

    tables = target_sheet.get("tables", [])
    if not tables:
        raise ValueError(f'Sheet "{target_sheet_name}" does not contain a table.')

    table_id = tables[0]["tableId"]
    # print(table_id)

    values = [
        movie_info["date"],
        movie_info["name"],
        movie_info["director"],
        movie_info["year"],
        movie_info["rating"],
        movie_info["quality"],
        movie_info["comments"],
    ]

    body = {
        "requests": [
            {
                "appendCells": {
                    "sheetId": target_sheet["properties"]["sheetId"],
                    "tableId": table_id,
                    "rows": [{"values": [make_cell(value) for value in values]}],
                    "fields": "userEnteredValue",
                }
            }
        ]
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=read_id(status),
        body=body,
    ).execute()

    return {
        "message": "success",
        "status": status,
        "movie_info": {
            "date": movie_info["date"],
            "name": movie_info["name"],
            "director": movie_info["director"],
            "year": movie_info["year"],
            "rating": movie_info["rating"],
            "quality": movie_info["quality"],
            "comments": movie_info["comments"],
        },
    }


if __name__ == "__main__":
    movie_info = {
        "sheetname": "2026",
        "date": "2026/3/19",
        "rating": 4.2,
        "comments": "test comment",
        "quality": "1080p",
        "name": "Project Hail Mary",
        "year": 2026,
        "director": "Phil Lord",
    }
    status = "movie"
    append_row(movie_info, status)
