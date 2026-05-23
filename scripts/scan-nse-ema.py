#!/usr/bin/env python3
"""Generate static NSE EMA crossover scanner data.

The website is hosted on GitHub Pages, so the expensive market scan happens here
inside GitHub Actions. The browser only loads the generated JSON after a user
chooses a scanner.
"""

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen

NSE_EQUITY_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
INDEX_URLS = {
    "large": "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
    "mid": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv",
    "small": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv",
}
SCAN_RULES = {
    "100-200": {"fast": 100, "slow": 200, "label": "100 / 200 EMA cross"},
    "50-100": {"fast": 50, "slow": 100, "label": "50 / 100 EMA cross"},
}
DEFAULT_OUTPUT_DIR = Path("public/stocks/data")
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept": "text/csv,application/json,text/plain,*/*",
}


@dataclass(frozen=True)
class Stock:
    symbol: str
    name: str
    market_cap: str
    isin: str = ""


def fetch_text(url: str, timeout: int = 25) -> str:
    request = Request(url, headers=REQUEST_HEADERS)
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def normalise_row(row: dict[str, str]) -> dict[str, str]:
    return {str(key).strip(): str(value).strip() for key, value in row.items()}


def fetch_index_symbols(url: str) -> set[str]:
    try:
        text = fetch_text(url)
        reader = csv.DictReader(text.splitlines())
        return {normalise_row(row).get("Symbol", "").upper() for row in reader if normalise_row(row).get("Symbol")}
    except Exception:
        return set()


def fetch_market_cap_sets() -> dict[str, set[str]]:
    return {bucket: fetch_index_symbols(url) for bucket, url in INDEX_URLS.items()}


def classify_symbol(symbol: str, cap_sets: dict[str, set[str]]) -> str:
    if symbol in cap_sets.get("large", set()):
        return "large"
    if symbol in cap_sets.get("mid", set()):
        return "mid"
    if symbol in cap_sets.get("small", set()):
        return "small"
    return "other"


def fetch_nse_universe(limit: int | None = None) -> list[Stock]:
    text = fetch_text(NSE_EQUITY_URL)
    cap_sets = fetch_market_cap_sets()
    stocks: list[Stock] = []

    for raw_row in csv.DictReader(text.splitlines()):
        row = normalise_row(raw_row)
        if row.get("SERIES") != "EQ":
            continue
        symbol = row.get("SYMBOL", "").upper()
        if not symbol:
            continue
        stocks.append(
            Stock(
                symbol=symbol,
                name=row.get("NAME OF COMPANY", symbol),
                market_cap=classify_symbol(symbol, cap_sets),
                isin=row.get("ISIN NUMBER", ""),
            )
        )

    stocks = sorted(stocks, key=lambda stock: stock.symbol)
    if limit:
        return stocks[:limit]
    return stocks


def chunked(items: list[Stock], size: int) -> Iterable[list[Stock]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def parse_price_response(response: dict) -> tuple[list[float], list[int]] | None:
    timestamps = response.get("timestamp") or []
    quote_data = (response.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote_data.get("close") or []
    rows = []
    for index, close in enumerate(closes):
        if close is None or index >= len(timestamps):
            continue
        value = float(close)
        if math.isfinite(value):
            rows.append((value, int(timestamps[index])))
    if not rows:
        return None
    return [row[0] for row in rows], [row[1] for row in rows]


def yahoo_symbol_to_nse(raw_symbol: str) -> str:
    decoded = unquote(raw_symbol or "")
    return decoded[:-3].upper() if decoded.upper().endswith(".NS") else decoded.upper()


def fetch_yahoo_batch(stocks: list[Stock]) -> tuple[dict[str, tuple[list[float], list[int]]], list[dict[str, str]]]:
    encoded_symbols = ",".join(quote(f"{stock.symbol}.NS", safe=".-") for stock in stocks)
    url = f"https://query1.finance.yahoo.com/v7/finance/spark?symbols={encoded_symbols}&range=2y&interval=1d"
    request = Request(url, headers={"User-Agent": REQUEST_HEADERS["User-Agent"], "Accept": "application/json,*/*"})
    price_data: dict[str, tuple[list[float], list[int]]] = {}
    failures: list[dict[str, str]] = []

    try:
        with urlopen(request, timeout=35) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        if len(stocks) > 1:
            midpoint = len(stocks) // 2
            left_prices, left_failures = fetch_yahoo_batch(stocks[:midpoint])
            right_prices, right_failures = fetch_yahoo_batch(stocks[midpoint:])
            left_prices.update(right_prices)
            return left_prices, left_failures + right_failures
        return price_data, [{"symbol": stock.symbol, "error": f"batch fetch failed: {exc}"} for stock in stocks]

    for result in payload.get("spark", {}).get("result", []):
        symbol = yahoo_symbol_to_nse(result.get("symbol", ""))
        responses = result.get("response") or []
        if not symbol or not responses:
            continue
        parsed = parse_price_response(responses[0])
        if parsed:
            price_data[symbol] = parsed

    found = set(price_data)
    for stock in stocks:
        if stock.symbol not in found:
            failures.append({"symbol": stock.symbol, "error": "no Yahoo daily candle data returned"})

    return price_data, failures


def fetch_all_prices(universe: list[Stock], batch_size: int = 20) -> tuple[dict[str, tuple[list[float], list[int]]], list[dict[str, str]]]:
    all_prices: dict[str, tuple[list[float], list[int]]] = {}
    failures: list[dict[str, str]] = []

    batches = list(chunked(universe, batch_size))
    for index, batch in enumerate(batches, start=1):
        prices, batch_failures = fetch_yahoo_batch(batch)
        all_prices.update(prices)
        failures.extend(batch_failures)
        print(f"Fetched batch {index}/{len(batches)}: {len(prices)} symbols")
        time.sleep(0.18)

    return all_prices, failures


def ema(values: list[float], period: int) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if len(values) < period:
        return output
    seed = sum(values[:period]) / period
    output[period - 1] = seed
    multiplier = 2 / (period + 1)
    for index in range(period, len(values)):
        previous = output[index - 1]
        if previous is None:
            continue
        output[index] = (values[index] - previous) * multiplier + previous
    return output


def find_cross(closes: list[float], timestamps: list[int], fast_period: int, slow_period: int, window: int = 15) -> dict | None:
    fast_ema = ema(closes, fast_period)
    slow_ema = ema(closes, slow_period)
    start = max(1, len(closes) - window)

    for index in range(start, len(closes)):
        if None in (fast_ema[index - 1], slow_ema[index - 1], fast_ema[index], slow_ema[index]):
            continue
        previous = float(fast_ema[index - 1]) - float(slow_ema[index - 1])
        current = float(fast_ema[index]) - float(slow_ema[index])
        if previous <= 0 and current > 0:
            return {
                "type": "bullish",
                "sessionsAgo": len(closes) - 1 - index,
                "fastEma": fast_ema[index],
                "slowEma": slow_ema[index],
                "close": closes[index],
                "timestamp": timestamps[index],
            }
        if previous >= 0 and current < 0:
            return {
                "type": "bearish",
                "sessionsAgo": len(closes) - 1 - index,
                "fastEma": fast_ema[index],
                "slowEma": slow_ema[index],
                "close": closes[index],
                "timestamp": timestamps[index],
            }
    return None


def stock_to_json(stock: Stock) -> dict[str, str]:
    return {"symbol": stock.symbol, "name": stock.name, "marketCap": stock.market_cap, "isin": stock.isin}


def build_scan_payload(
    scan_id: str,
    universe: list[Stock],
    price_data: dict[str, tuple[list[float], list[int]]],
    fetch_failures: list[dict[str, str]],
    generated_at: str,
) -> dict:
    rule = SCAN_RULES[scan_id]
    fast_period = rule["fast"]
    slow_period = rule["slow"]
    results = []
    skipped = []

    for stock in universe:
        candles = price_data.get(stock.symbol)
        if not candles:
            continue
        closes, timestamps = candles
        if len(closes) < slow_period + 15:
            skipped.append({"symbol": stock.symbol, "reason": f"needs at least {slow_period + 15} daily candles"})
            continue
        cross = find_cross(closes, timestamps, fast_period, slow_period)
        if cross:
            results.append({**stock_to_json(stock), **cross})

    bucket_counts = {
        bucket: sum(1 for stock in universe if stock.market_cap == bucket)
        for bucket in ("large", "mid", "small", "other")
    }

    return {
        "market": "NSE India",
        "scanId": scan_id,
        "label": rule["label"],
        "rule": f"{fast_period} EMA / {slow_period} EMA crossover within last 15 daily sessions",
        "fastPeriod": fast_period,
        "slowPeriod": slow_period,
        "windowSessions": 15,
        "generatedAt": generated_at,
        "dataSource": {
            "universe": NSE_EQUITY_URL,
            "prices": "Yahoo Finance chart/spark daily candles",
            "capBuckets": "NIFTY 100, NIFTY Midcap 150, NIFTY Smallcap 250; remaining NSE EQ securities are grouped as Other",
        },
        "universeSize": len(universe),
        "pricedUniverseSize": len(price_data),
        "universe": [stock_to_json(stock) for stock in universe],
        "marketCapBuckets": bucket_counts,
        "resultCount": len(results),
        "failureCount": len(fetch_failures),
        "skippedCount": len(skipped),
        "results": sorted(results, key=lambda item: (item["sessionsAgo"], item["symbol"])),
        "failures": fetch_failures[:80],
        "skipped": skipped[:80],
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate NSE EMA crossover JSON data for GitHub Pages.")
    parser.add_argument("--limit", type=int, default=None, help="Optional local test limit for number of NSE EQ symbols.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for JSON files.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    generated_at = datetime.now(timezone.utc).isoformat()
    universe = fetch_nse_universe(limit=args.limit)
    prices, failures = fetch_all_prices(universe)

    manifest = {
        "market": "NSE India",
        "generatedAt": generated_at,
        "universeSize": len(universe),
        "pricedUniverseSize": len(prices),
        "failureCount": len(failures),
        "availableScans": [],
    }

    for scan_id in SCAN_RULES:
        payload = build_scan_payload(scan_id, universe, prices, failures, generated_at)
        file_name = f"ema-{scan_id}-crosses.json"
        write_json(output_dir / file_name, payload)
        manifest["availableScans"].append(
            {
                "scanId": scan_id,
                "label": payload["label"],
                "file": file_name,
                "resultCount": payload["resultCount"],
                "rule": payload["rule"],
            }
        )
        print(json.dumps({"scanId": scan_id, "results": payload["resultCount"]}, indent=2))

    # Backward-compatible alias for the first scanner used by the original UI.
    write_json(output_dir / "ema-crosses.json", build_scan_payload("100-200", universe, prices, failures, generated_at))
    write_json(output_dir / "scan-manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
