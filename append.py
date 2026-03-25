from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
SERVICE_ACCOUNT_FILE = "movie-491021-a3b07c0b565a.json"

data = {}
with open("spreadsheetid.txt", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]
for i in range(0, len(lines), 2):
    key = lines[i].rstrip(":")
    value = lines[i + 1]
    data[key] = value

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]



def read_id(name):
    data = {}
    with open("spreadsheetid.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    for i in range(0, len(lines), 2):
        key = lines[i].rstrip(":")
        value = lines[i + 1]
        data[key] = value
    return data[name]



def make_cell(value):
    if isinstance(value, (int, float)):
        return {"userEnteredValue": {"numberValue": value}}
    return {"userEnteredValue": {"stringValue": str(value)}}


def append_row(movie_info, status):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

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

    tableId = tables[0]["tableId"]

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
                    "tableId": tableId,
                    "rows": [{"values": [make_cell(value) for value in values]}],
                    "fields": "userEnteredValue",
                }
            }
        ]
    }

    result = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=read_id(status), body=body)
        .execute()
    )

    # print(result)
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
        "sheetname": "Sheet1",
        "date": "2026/3/19",
        "rating": 4.2,
        "comments": "test comment",
        "quality": "1080p",
        "name": "挽救计划 Project Hail Mary",
        "year": 2026,
        "director": "Phil Lord",
    }
    status = "test"
    append_row(movie_info, status)

