# Movie

A small Python app for managing movie logs from Douban.

It currently supports two workflows:

- Web app: parse movie info from a Douban subject ID/URL and append the result to Google Sheets
- WeChat script: read movie records from Google Sheets, build an article page, upload images, and save a draft to a WeChat Official Account

## Stack

- Python
- Flask
- Selenium
- Google Sheets API
- pywebview

## Project Structure

```text
.
|-- app.py                  # Flask entry
|-- desktop.py              # Desktop wrapper
|-- wechat.py               # WeChat draft workflow
|-- routes/                 # HTTP routes
|-- services/               # Business logic
|-- crawlers/               # Douban crawling
|-- utils/                  # Google Sheets helpers
|-- templates/              # Web and article templates
|-- static/                 # Frontend assets
`-- configs/                # Local config files
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure Chrome/Chromium and a matching ChromeDriver are available.
4. Put local config files in `configs/`.

## Config

This project reads local credentials from `configs/ids.json` by default.

Typical values used in the current code:

- Google Sheets IDs
- WeChat `AppID` / `AppSecret`
- Local draft data file at `configs/data.json`
- Google service account JSON file in `configs/`

Optional environment variables:

- `HOST`
- `PORT`
- `APP_RUN_MODE`
- `DRAFT_DATA_FILE`
- `CHROME_BIN`
- `CHROMEDRIVER_PATH`
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `SPREADSHEET_IDS_JSON`

## Run

Start the web app:

```bash
python app.py
```

Open `http://127.0.0.1:5000`.

Start the desktop wrapper:

```bash
python desktop.py
```

Run the WeChat draft flow:

```bash
python wechat.py
```

The script will prompt for a digest, read movie data from Google Sheets, generate article HTML, upload images, and create a WeChat draft.

## API

- `GET /` main page
- `GET /health` health check
- `POST /api/movie` fetch movie info from Douban
- `POST /api/submit` append a movie row to Google Sheets
- `GET /api/load` load local draft data
- `POST /api/save` save local draft data
- `POST /api/client-ping` desktop keep-alive

## Notes

- The crawler is built for Douban movie pages.
- `wechat.py` depends on valid WeChat Official Account credentials.
- Files in `configs/` should be treated as private.
