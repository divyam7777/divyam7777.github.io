"""
Check whether the NSE (Indian stock market) traded today.

Fetches the latest Nifty 50 candle from Yahoo Finance and compares
its timestamp to today's date in IST (Asia/Kolkata).

Exit codes:
  0 – market was OPEN today   → pipeline should continue
  1 – market was CLOSED today → pipeline should skip the scanner
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen

IST = timezone(timedelta(hours=5, minutes=30))
SYMBOL = "^NSEI"
URL = (
    f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}"
    "?range=5d&interval=1d"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,*/*",
}


def main() -> None:
    today_ist = datetime.now(IST).date()
    print(f"Today (IST): {today_ist.isoformat()}")

    try:
        req = Request(URL, headers=HEADERS)
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        # If we can't reach Yahoo at all, let the pipeline continue
        # so the scanner itself can surface the error properly.
        print(f"[WARN] Could not reach Yahoo Finance: {exc}")
        print("OPEN (assuming open -- could not verify)")
        sys.exit(0)

    try:
        timestamps = data["chart"]["result"][0]["timestamp"]
    except (KeyError, IndexError, TypeError):
        print("[WARN] Unexpected response structure from Yahoo Finance")
        print("OPEN (assuming open -- could not verify)")
        sys.exit(0)

    # Convert the latest candle timestamp to an IST date
    latest_ts = timestamps[-1]
    latest_date = datetime.fromtimestamp(latest_ts, tz=IST).date()
    print(f"Latest trading session (IST): {latest_date.isoformat()}")

    if latest_date == today_ist:
        print("[OK] Market is OPEN today -- scanner will proceed.")
        sys.exit(0)
    else:
        print(
            f"[SKIP] Market is CLOSED today (latest session was {latest_date}). "
            "Skipping scanner."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
