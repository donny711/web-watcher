# web-watcher

Monitor websites for content changes. Get notified in your terminal — and optionally by email — when a page updates.

## Demo

![web-watcher demo](assets/demo.png)

## Requirements

- Python 3.9 or newer
- pip

## Installation

```bash
git clone  https://github.com/donny711/web-watcher
cd web-watcher
pip install -r requirements.txt
```

## Quick Start

Watch a single URL every 5 minutes (default):

```bash
python3 watcher.py https://example.com
```

Watch multiple URLs every 30 seconds:

```bash
python3 watcher.py https://example.com https://news.ycombinator.com -i 30s
```

Run a one-shot check and exit:

```bash
python3 watcher.py https://example.com --once
```

## Interval Format

| Flag     | Meaning    |
|----------|------------|
| `-i 30s` | 30 seconds |
| `-i 5m`  | 5 minutes  |
| `-i 2h`  | 2 hours    |
| `-i 60`  | 60 seconds |

## Snapshots

Snapshots are stored in `snapshots/` by default (one `.txt` file per URL, named by MD5 hash). Change location with `--snapshots-dir`:

```bash
python3 watcher.py https://example.com --snapshots-dir /tmp/my-snapshots
```

## Email Notifications (Gmail)

1. Enable 2-Factor Authentication on your Google account
2. Generate an **App Password** at https://myaccount.google.com/apppasswords
3. Run with email flags:

```bash
python3 watcher.py https://example.com   --email-from you@gmail.com   --email-to recipient@example.com   --email-password "your-16-char-app-password"
```

## Run Tests

```bash
python3 -m pytest -v
```

## Project Structure

```
web-watcher/
├── fetcher.py          # HTTP download + HTML text extraction
├── differ.py           # Colored diff computation
├── notifier.py         # Terminal + email notifications
├── watcher.py          # CLI entry point + main loop
├── snapshots/          # Auto-created; stores per-URL snapshots
├── tests/
│   ├── test_fetcher.py
│   ├── test_differ.py
│   ├── test_notifier.py
│   └── test_watcher.py
└── requirements.txt
```
