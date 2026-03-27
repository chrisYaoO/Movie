# Movie Parser

Movie Parser is a lightweight Flask application for collecting movie entries, parsing metadata from Douban, and appending the final record to Google Sheets. It supports both browser-based usage and a small desktop wrapper powered by `pywebview`.

## Features

- Parse movie title, director, and release year from a Douban movie URL or subject ID
- Submit movie records to a target Google Sheet
- Save drafts locally and, in desktop mode, persist them on the server
- Run as a standard web app or as a desktop-style local application
- Deploy with Docker and Gunicorn

## Tech Stack

- Python 3.11
- Flask
- Selenium + Chromium
- Beautiful Soup
- Google Sheets API
- pywebview

## Project Structure

```text
.
|-- app.py                  # Flask app entry point
|-- desktop.py              # Desktop launcher
|-- routes/                 # HTTP routes
|-- services/               # Business logic and draft storage
|-- crawlers/               # Douban parsing logic
|-- utils/                  # Google Sheets append helper
|-- templates/              # HTML templates
|-- static/                 # Frontend assets
|-- configs/                # Local config and credential files
`-- Dockerfile              # Container deployment
```

## Requirements

- Python 3.11+
- Google Chrome / Chromium
- ChromeDriver compatible with the installed browser
- A Google service account with access to the target spreadsheet

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

The application supports environment variables for deployment and secrets management.

| Variable | Description | Default |
| --- | --- | --- |
| `HOST` | Flask bind host in server mode | `0.0.0.0` |
| `PORT` | Flask bind port | `5000` |
| `APP_RUN_MODE` | Run mode: `server` or `desktop` | `server` |
| `DRAFT_DATA_FILE` | Draft persistence file path | `configs/data.json` |
| `CHROME_BIN` | Path to Chrome/Chromium binary | auto/default |
| `CHROMEDRIVER_PATH` | Path to ChromeDriver | auto/default |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Raw service account JSON string | not set |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to service account JSON file | `configs/movie-491021-a3b07c0b565a.json` |
| `SPREADSHEET_IDS_JSON` | JSON mapping of spreadsheet IDs | not set |

If `SPREADSHEET_IDS_JSON` is not provided, the app reads spreadsheet IDs from `configs/ids.json`.

## Running the App

### Web Mode

```bash
python app.py
```

Then open `http://127.0.0.1:5000`.

### Desktop Mode

```bash
python desktop.py
```

This starts the Flask backend locally and opens the UI inside a desktop window.

## Docker

Build and run:

```bash
docker build -t movie-parser .
docker run -p 8000:8000 movie-parser
```

The container uses Gunicorn and listens on port `8000`.

## API Overview

- `GET /` : Main application page
- `GET /health` : Health check
- `POST /api/movie` : Parse movie metadata from a Douban URL or subject ID
- `POST /api/submit` : Submit a movie record to Google Sheets
- `GET /api/load` : Load saved draft data
- `POST /api/save` : Save draft data
- `POST /api/client-ping` : Keep desktop sessions alive

## Notes

- The parser is designed for Douban movie pages.
- Google Sheets must already contain the target sheet and table structure expected by the app.
- Credentials in `configs/` should be treated as sensitive and should not be committed to public repositories.
