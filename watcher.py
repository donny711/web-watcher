import argparse
import difflib
import hashlib
import os
import re
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup


SNAPSHOTS_DIR = "snapshots"


SKIP_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript"]


def get_page_text(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    except Exception as e:
        print(f"[error] couldn't fetch {url}: {e}")
        return None

    if r.status_code != 200:
        print(f"[warn] got {r.status_code} for {url}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(SKIP_TAGS):
        tag.decompose()

    text = soup.get_text(" ")
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_diff(old, new):

    lines_old = old.splitlines(keepends=True)
    lines_new = new.splitlines(keepends=True)

    result = []
    for line in difflib.unified_diff(lines_old, lines_new, lineterm=""):
        if line.startswith("+") and not line.startswith("+++"):
            result.append(f"\033[32m{line}\033[0m")
        elif line.startswith("-") and not line.startswith("---"):
            result.append(f"\033[31m{line}\033[0m")
        elif line.startswith("@"):
            result.append(f"\033[36m{line}\033[0m")

    if not result:
        return []

    if len(result) > 20:
        extra = len(result) - 20
        result = result[:20]
        result.append(f"  ... and {extra} more lines")

    return result


def print_diff(url, diff_lines):
    if not diff_lines:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{ts}] \033[1mchange detected: {url}\033[0m")
    for line in diff_lines:
        print(line)
    print()


def send_email(url, diff_lines, from_addr, to_addr, password):
  
    clean = re.sub(r"\033\[[0-9;]*m", "", "\n".join(diff_lines))
    body = f"change at {url}\n\n{clean}"
    msg = MIMEText(body)
    msg["Subject"] = f"[web-watcher] {url}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(from_addr, password)
            s.sendmail(from_addr, to_addr, msg.as_string())
        print(f"[email] sent to {to_addr}")
    except Exception as e:
        print(f"[warn] email failed: {e}")


def snap_path(url):
    h = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(SNAPSHOTS_DIR, h + ".txt")


def load_snap(url):
    p = snap_path(url)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


def save_snap(url, text):
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    with open(snap_path(url), "w", encoding="utf-8") as f:
        f.write(text)


def check(url, email_cfg=None):
    current = get_page_text(url)
    if current is None:
        return

    previous = load_snap(url)
    if previous is None:
        save_snap(url, current)
        print(f"[ok] saved first snapshot for {url}")
        return

    diff = get_diff(previous, current)
    if diff:
        print_diff(url, diff)
        if email_cfg:
            send_email(url, diff, **email_cfg)
        save_snap(url, current)
    else:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] no changes: {url}")


def parse_interval(val):
    m = re.fullmatch(r"(\d+)([smh]?)", val.strip())
    if not m:
        raise ValueError(f"bad interval: {val}")
    n = int(m.group(1))
    unit = m.group(2)
    return n * {"s": 1, "m": 60, "h": 3600, "": 1}[unit]


def main():
    p = argparse.ArgumentParser(description="watch urls for changes")
    p.add_argument("urls", nargs="+")
    p.add_argument("-i", "--interval", default="5m", help="e.g. 30s, 5m, 1h")
    p.add_argument("--email-from")
    p.add_argument("--email-to")
    p.add_argument("--email-password")
    p.add_argument("--once", action="store_true")
    args = p.parse_args()

    try:
        interval = parse_interval(args.interval)
    except ValueError as e:
        p.error(str(e))

    email_cfg = None
    if args.email_from and args.email_to and args.email_password:
        email_cfg = {
            "from_addr": args.email_from,
            "to_addr": args.email_to,
            "password": args.email_password,
        }

    print(f"watching {len(args.urls)} url(s) every {args.interval} -- ctrl+c to stop")
    for url in args.urls:
        check(url, email_cfg)

    if args.once:
        return

    try:
        while True:
            time.sleep(interval)
            for url in args.urls:
                check(url, email_cfg)
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
