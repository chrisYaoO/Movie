import json
import os
from datetime import date
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import re
from crawlers.crawler import parse_movie_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SERVICE_ACCOUNT_FILE = os.path.join(
    BASE_DIR, "configs", "movie-491021-1cd922995007.json"
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
        parse_movie_url(movie_info["url"]),
        movie_info.get("image", ""),
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
            "image": movie_info.get("image", ""),
        },
    }


def valid_month(month):
    return month in range(1, 13)


def get_year_month():

    year, month = user_input()
    today = date.today()

    if year is None:
        
        curr_year = str(today.year)
    else:
        curr_year = str(year)

    if month is None:
        month_start, month_end = today.month, today.month
    elif len(month) == 1:
        if valid_month(month[0]):
            month_start, month_end = month[0], month[0]
        else:
            raise ValueError(f"Invalid month: {month[0]}")
    elif len(month) == 2:
        if valid_month(month[0]) and valid_month(month[1]):
            month_start, month_end = month[0], month[1]
        else:
            raise ValueError(f"Invalid month: {month}")
    else:
        raise ValueError(f"Invalid month: {month}")

    return curr_year, month_start, month_end


def get_title(curr_year, month_start, month_end):
    if month_start == month_end:
        return f"{curr_year} {month_start}月观影"
    else:
        return f"{curr_year} {month_start}-{month_end}月观影"


def user_input():
    try:
        y_in = input("year: ").strip()
        year = int(y_in) if y_in else None

        m_in = input("month: ").strip()
        if m_in:
            month = list(map(int, m_in.split()))
        else:
            month = None

        # print(f" year={year}, month={month}")

    except ValueError:
        print("Enter integers for year and month")
    return year, month


def split_name(name):

    parts = name.split()

    foreign_pattern = r"[a-zA-Z\u3040-\u30FF\uAC00-\uD7AF]"

    split_index = len(parts)

    for i, part in enumerate(parts):
        if re.search(foreign_pattern, part):
            split_index = i
            break

    main_name = " ".join(parts[:split_index])
    sub_name = " ".join(parts[split_index:])

    return main_name, sub_name


def extract(status):

    curr_year, month_start, month_end = get_year_month()

    print((curr_year, month_start, month_end))

    creds = load_service_account_credentials()

    service = build("sheets", "v4", credentials=creds)
    res = service.spreadsheets().get(spreadsheetId=read_id(status)).execute()
    target_sheet_name = curr_year
    target_sheet = None

    for sheet in res["sheets"]:
        if sheet.get("properties", {}).get("title") == target_sheet_name:
            target_sheet = sheet
            break

    if target_sheet is None:
        raise ValueError(f'Sheet "{target_sheet_name}" not found.')

    # tables = target_sheet.get("tables", [])
    # if not tables:
    #     raise ValueError(f'Sheet "{target_sheet_name}" does not contain a table.')

    # # print(tables)
    # table_id = tables[0]["tableId"]

    result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=read_id(status),
            range=f"{target_sheet_name}!A1:I",
        )
        .execute()
    )

    values = result.get("values", [])

    headers = [v.lower() for v in values[0]]

    backup = []
    movie_list = []

    for row in values[1:]:
        row_dict = dict(zip(headers, row))

        name, subname = split_name(row_dict["name"])
        row_dict["name"] = name
        row_dict["subname"] = subname

        # print(row_dict["date"].split("/")[0])
        curr_month = int(row_dict["date"].split("/")[0])

        if month_start <= curr_month <= month_end:
            movie_list.append(row_dict)

        backup.append(row_dict)

    if movie_list is []:
        raise ValueError(f"No movie in month{month_start}-{month_end}!")

    with open(f"configs/backup_{target_sheet_name}.json", "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2, ensure_ascii=False)

    # print("movie sheet updated")

    title = get_title(curr_year, month_start, month_end)

    return movie_list, title


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

    # titles = [
    #     "熊家餐馆 第一季 The Bear Season 1",  # 包含英文和数字
    #     "一公升的眼泪 1リットルの涙",  # 外文部分以数字开头
    #     "寄生虫 蓝光版 기생충",  # 中文部分有多个空格，纯韩文
    #     "千与千寻 千と千尋の神隠し",  # 日文
    #     "只有中文标题",  # 没有外文的情况
    # ]

    # for title in titles:
    #     zh, foreign = split_name(title)
    #     print(f"原文本: {title}")
    #     print(f"-> 中文: '{zh}'")
    #     print(f"-> 外文: '{foreign}'\n")
