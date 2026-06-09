import json
import os

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SERVICE_ACCOUNT_FILE = os.path.join(
    BASE_DIR,
    "configs",
    "movie-491021-1cd922995007.json",
)
DEFAULT_SPREADSHEET_IDS_FILE = os.path.join(BASE_DIR, "configs", "ids.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def load_service_account_credentials():
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        return Credentials.from_service_account_info(
            json.loads(service_account_json),
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


def read_draft_sheet(status, year):
    credentials = load_service_account_credentials()
    service = build("sheets", "v4", credentials=credentials)
    spreadsheet_id = read_id(status)
    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    if not any(
        sheet.get("properties", {}).get("title") == year
        for sheet in metadata["sheets"]
    ):
        raise ValueError(f'Sheet "{year}" not found.')

    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{year}!A1:I")
        .execute()
    )
    values = result.get("values", [])
    if not values:
        raise ValueError(f'Sheet "{year}" has no header row.')
    return values[0], values[1:]


def prompt_draft_period():
    from services.draft_selection import DraftPeriod

    return DraftPeriod.from_inputs(input("year: "), input("month: "))


def extract(status, period=None):
    from services.draft_selection import select_draft_movies

    period = period or prompt_draft_period()
    headers, rows = read_draft_sheet(status, period.year)
    return select_draft_movies(headers, rows, period), period.title
