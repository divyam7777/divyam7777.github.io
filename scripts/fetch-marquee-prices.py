#!/usr/bin/env python3
"""Fetch real-time prices for the home page ticker marquee.

Fetches latest prices and 10-day sparkline data for a curated list of
Indian (NSE) and US stocks using Yahoo Finance chart API.
Outputs a static JSON file that the home page reads on load.
"""

import json
import math
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

OUTPUT_DIR = Path("public/data")
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept": "application/json,*/*",
}

# Curated tickers for the marquee
INDIA_TICKERS = [
    {"sym": "RELIANCE",   "name": "Reliance Ind.",    "yahoo": "RELIANCE.NS"},
    {"sym": "TCS",        "name": "Tata Consultancy", "yahoo": "TCS.NS"},
    {"sym": "HDFCBANK",   "name": "HDFC Bank",        "yahoo": "HDFCBANK.NS"},
    {"sym": "INFY",       "name": "Infosys",          "yahoo": "INFY.NS"},
    {"sym": "ICICIBANK",  "name": "ICICI Bank",       "yahoo": "ICICIBANK.NS"},
    {"sym": "TATAMOTORS", "name": "Tata Motors",      "yahoo": "TATAMOTORS.NS"},
    {"sym": "SBIN",       "name": "State Bank",       "yahoo": "SBIN.NS"},
    {"sym": "BHARTIARTL", "name": "Bharti Airtel",    "yahoo": "BHARTIARTL.NS"},
    {"sym": "LT",         "name": "Larsen & Toubro",  "yahoo": "LT.NS"},
    {"sym": "WIPRO",      "name": "Wipro",            "yahoo": "WIPRO.NS"},
]

US_TICKERS = [
    {"sym": "AAPL",  "name": "Apple Inc.",      "yahoo": "AAPL"},
    {"sym": "TSLA",  "name": "Tesla Inc.",      "yahoo": "TSLA"},
    {"sym": "MSFT",  "name": "Microsoft",       "yahoo": "MSFT"},
    {"sym": "GOOGL", "name": "Alphabet",        "yahoo": "GOOGL"},
    {"sym": "AMZN",  "name": "Amazon",          "yahoo": "AMZN"},
    {"sym": "NVDA",  "name": "NVIDIA",          "yahoo": "NVDA"},
    {"sym": "META",  "name": "Meta Platforms",   "yahoo": "META"},
    {"sym": "NFLX",  "name": "Netflix",         "yahoo": "NFLX"},
    {"sym": "AMD",   "name": "AMD Inc.",        "yahoo": "AMD"},
    {"sym": "JPM",   "name": "JPMorgan Chase",  "yahoo": "JPM"},
]


def fetch_chart(yahoo_symbol: str) -> dict | None:
    """Fetch 1-month daily chart data from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(yahoo_symbol, safe='.-')}?range=1mo&interval=1d"
    try:
        time.sleep(random.uniform(0.05, 0.15))
        request = Request(url, headers=REQUEST_HEADERS)
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
            result = payload.get("chart", {}).get("result")
            if not result:
                return None
            return result[0]
    except Exception as exc:
        print(f"  ⚠ Failed to fetch {yahoo_symbol}: {exc}")
        return None


def extract_ticker_data(ticker: dict, currency_prefix: str) -> dict | None:
    """Extract price, change, and sparkline from Yahoo chart data."""
    data = fetch_chart(ticker["yahoo"])
    if not data:
        return None

    meta = data.get("meta", {})
    quote_data = (data.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote_data.get("close") or []

    # Filter valid closes
    valid_closes = [c for c in closes if c is not None and math.isfinite(c)]
    if len(valid_closes) < 2:
        return None

    current_price = valid_closes[-1]
    prev_close = meta.get("chartPreviousClose") or valid_closes[-2]
    change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0

    # Sparkline: last 10 data points, normalized to 0-28 range
    spark_points = valid_closes[-10:] if len(valid_closes) >= 10 else valid_closes
    spark_min = min(spark_points)
    spark_max = max(spark_points)
    spark_range = spark_max - spark_min or 1
    spark_normalized = [round(((v - spark_min) / spark_range) * 24 + 2, 1) for v in spark_points]

    # Format price
    if current_price >= 1000:
        price_str = f"{currency_prefix}{current_price:,.0f}"
    else:
        price_str = f"{currency_prefix}{current_price:,.2f}"

    return {
        "sym": ticker["sym"],
        "name": ticker["name"],
        "price": price_str,
        "change": f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%",
        "up": change_pct >= 0,
        "spark": ",".join(str(v) for v in spark_normalized),
    }


def main():
    print("Fetching real-time marquee prices...")
    print()

    india_results = []
    print("[IN] India stocks:")
    for ticker in INDIA_TICKERS:
        print(f"  Fetching {ticker['sym']}...", end=" ")
        result = extract_ticker_data(ticker, "₹")
        if result:
            india_results.append(result)
            print(f"✓ {result['price']} ({result['change']})")
        else:
            print("✗ failed")

    print()
    us_results = []
    print("[US] US stocks:")
    for ticker in US_TICKERS:
        print(f"  Fetching {ticker['sym']}...", end=" ")
        result = extract_ticker_data(ticker, "$")
        if result:
            us_results.append(result)
            print(f"✓ {result['price']} ({result['change']})")
        else:
            print("✗ failed")

    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "india": india_results,
        "us": us_results,
    }

    output_path = OUTPUT_DIR / "marquee-prices.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\n✓ Wrote {output_path} ({len(india_results)} IN + {len(us_results)} US tickers)")


if __name__ == "__main__":
    main()
