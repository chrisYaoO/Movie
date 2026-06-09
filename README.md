# WeChat Movie Draft

Creates one WeChat Official Account movie draft from movie records stored in
Google Sheets.

## Workflow

A Draft Run:

1. Prompts for Digest, year, and one or two months.
2. Reads and validates Draft Movies from Google Sheets.
3. Downloads and uploads every movie poster.
4. Writes the Preview to `outputs/movie_wechat.html`.
5. Creates one WeChat draft.

Blank year/month inputs use the current year/month. An empty Digest is sent to
WeChat as a single space.

## Setup

Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Provide:

- `configs/ids.json` with Google Sheets IDs, WeChat `AppID`, `AppSecret`,
  `author`, `thumb_media_id`, and `source_url`
- a Google service account JSON file at
  `configs/movie-491021-1cd922995007.json`

Optional configuration:

- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `SPREADSHEET_IDS_JSON`

## Run

```bash
python wechat.py
```

The Windows launcher `run_wechat.vbs` starts the same command.

If a poster upload fails, no draft is created. Rerun to upload all posters from
the beginning. If draft creation times out, inspect the WeChat Official Account
backend before rerunning because the result is unknown.

## Tests

```bash
python -m unittest discover -v
```

Automated tests use fake Google Sheets, Douban, and WeChat adapters. They do not
create a real draft.
