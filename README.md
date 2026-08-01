# WeChat Movie Draft

Create a WeChat Official Account movie draft from viewing records stored in Google Sheets.

A Draft Run reads and validates movies, uploads posters, generates an HTML preview, and creates one WeChat draft. This repository contains only the WeChat draft workflow.

## Workflow

```mermaid
flowchart LR
    A[Enter Digest and Draft Period] --> B[Read and validate movies]
    B --> C[Download and upload posters]
    C --> D[Write HTML Preview]
    D --> E[Create WeChat draft]
```

- Preserves Google Sheets row order.
- Shows the current movie and stage in the command window.
- Writes the Preview to `outputs/movie_wechat.html`.
- Stops before draft creation if a poster upload fails.
- Never modifies Google Sheets or `templates/movie_template.html`.

## Project Layout

```text
.
|-- wechat.py                         # Command-line entry point
|-- list_wechat_images.py             # List permanent image media IDs
|-- run_wechat.command                # macOS launcher
|-- run_wechat.vbs                    # Windows launcher
|-- services/
|   |-- draft_selection.py            # Period and movie validation
|   |-- draft_workflow.py             # Draft Run coordinator
|   |-- poster_loader.py              # Poster download and compression
|   `-- wechat_client.py              # WeChat API client
|-- utils/google_sheets.py            # Read-only Google Sheets adapter
|-- templates/movie_template.html     # Source article template
`-- tests/                             # Offline tests
```

## Setup

Python 3.9 or newer is required.

macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `configs.example.json` to `configs/ids.json`, then replace the
placeholders with real values:

macOS/Linux:

```sh
mkdir -p configs
cp configs.example.json configs/ids.json
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force configs
Copy-Item configs.example.json configs/ids.json
```

`configs/ids.json`:

```json
{
  "movie": "GOOGLE_SPREADSHEET_ID",
  "AppID": "WECHAT_APP_ID",
  "AppSecret": "WECHAT_APP_SECRET",
  "author": "ARTICLE_AUTHOR",
  "thumb_media_id": "WECHAT_THUMB_MEDIA_ID",
  "source_url": "https://example.com"
}
```

- `movie`: Google Spreadsheet ID, taken from the spreadsheet URL.
- `AppID` and `AppSecret`: WeChat Official Account credentials.
- `author`: author name shown in the draft.
- `thumb_media_id`: existing WeChat thumbnail material ID.
- `source_url`: source link shown in the article.

Do not commit `configs/ids.json` or the Google service account JSON; the whole
`configs/` directory is ignored by Git.
Google service account file can be obtained from [Google Developer Console](https://console.developers.google.com/).
Place it at
`configs/movie-491021-22b25e7fe411.json`, or set
`GOOGLE_SERVICE_ACCOUNT_FILE` to the actual file path. Relative paths are
resolved from the project root.

Optional overrides:

| Variable | Purpose |
| --- | --- |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Complete service-account JSON string |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Service-account JSON file path |
| `SPREADSHEET_IDS_JSON` | JSON string containing spreadsheet IDs |

## Google Sheets Format

Each year uses a same-named sheet, such as `2026`.

| Field | Required | Notes |
| --- | --- | --- |
| `date` | Yes | `M/D` format |
| `name` | Yes | Movie title |
| `director` | Yes | Director display text |
| `year` | Yes | Release year |
| `rating` | Yes | Displayed rating |
| `comment` | Yes | May be empty |
| `movie_id` | Yes | Douban movie ID |
| `image_id` | Yes | Douban poster image ID |
| `quality` | No | Ignored |

## Run

macOS/Linux:

```sh
.venv/bin/python wechat.py
```

On macOS, double-click `run_wechat.command` to open Terminal and start the
interactive run automatically.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe wechat.py
```

On Windows, you can also double-click `run_wechat.vbs`.

To find a `thumb_media_id`, list the existing permanent image materials:

macOS/Linux:

```sh
.venv/bin/python list_wechat_images.py
.venv/bin/python list_wechat_images.py --match "部分图片 URL 或文件名"
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe list_wechat_images.py
.\.venv\Scripts\python.exe list_wechat_images.py --match "部分图片 URL 或文件名"
```

Copy the matching `media_id` into `thumb_media_id` in `configs/ids.json`.
The script queries permanent image materials and does not upload or modify
anything.

Example input:

```text
Digest: Monthly movie notes
year: 2026
month: 6
```

Leave year or month blank to use the current value. Enter two months such as `6 7` to select a same-year range. An empty Digest is sent to WeChat as a single space.

Progress is shown in the command window:

```text
Selected 4 movies.
[1/4] Movie Name: downloading poster...
[1/4] Movie Name: uploading poster to WeChat...
Writing Preview to outputs\movie_wechat.html...
Creating WeChat draft...
Draft created: MEDIA_ID
```

If draft creation times out, inspect the WeChat backend before rerunning because the result is unknown.

## Tests

macOS/Linux:

```sh
.venv/bin/python -m unittest discover -v
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Tests use fake external adapters and do not create real drafts.
