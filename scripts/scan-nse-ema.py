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
SCAN_WINDOW_SESSIONS = 60
DEFAULT_OUTPUT_DIR = Path("public/data")
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept": "text/csv,application/json,text/plain,*/*",
}


@dataclass(frozen=True)
class Stock:
    symbol: str
    name: str
    market_cap: str
    sector: str = "Unclassified"
    isin: str = ""


def fetch_text(url: str, timeout: int = 25) -> str:
    request = Request(url, headers=REQUEST_HEADERS)
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def normalise_row(row: dict[str, str]) -> dict[str, str]:
    return {str(key).strip(): str(value).strip() for key, value in row.items()}


def fetch_index_metadata(url: str) -> dict[str, dict[str, str]]:
    try:
        text = fetch_text(url)
        reader = csv.DictReader(text.splitlines())
        metadata = {}
        for raw_row in reader:
            row = normalise_row(raw_row)
            symbol = row.get("Symbol", "").upper()
            if not symbol:
                continue
            metadata[symbol] = {
                "sector": row.get("Industry") or "Unclassified",
            }
        return metadata
    except Exception:
        return {}


def fetch_market_metadata() -> dict[str, dict[str, str]]:
    metadata = {}
    for bucket, url in INDEX_URLS.items():
        for symbol, details in fetch_index_metadata(url).items():
            metadata[symbol] = {**details, "marketCap": bucket}
    return metadata


def classify_symbol(symbol: str, market_metadata: dict[str, dict[str, str]]) -> str:
    return market_metadata.get(symbol, {}).get("marketCap", "other")


def sector_for_symbol(symbol: str, market_metadata: dict[str, dict[str, str]]) -> str:
    return market_metadata.get(symbol, {}).get("sector", "Unclassified")


def fetch_nse_universe(limit: int | None = None) -> list[Stock]:
    text = fetch_text(NSE_EQUITY_URL)
    market_metadata = fetch_market_metadata()
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
                market_cap=classify_symbol(symbol, market_metadata),
                sector=sector_for_symbol(symbol, market_metadata),
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


def parse_price_response(response: dict) -> dict[str, list[float] | list[int]] | None:
    timestamps = response.get("timestamp") or []
    quote_data = (response.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote_data.get("close") or []
    volumes = quote_data.get("volume") or []
    rows = []
    for index, close in enumerate(closes):
        if close is None or index >= len(timestamps):
            continue
        value = float(close)
        if math.isfinite(value):
            volume = volumes[index] if index < len(volumes) and volumes[index] is not None else 0
            rows.append((value, int(timestamps[index]), int(volume)))
    if not rows:
        return None
    return {
        "closes": [row[0] for row in rows],
        "timestamps": [row[1] for row in rows],
        "volumes": [row[2] for row in rows],
    }


def yahoo_symbol_to_nse(raw_symbol: str) -> str:
    decoded = unquote(raw_symbol or "")
    return decoded[:-3].upper() if decoded.upper().endswith(".NS") else decoded.upper()


def fetch_chart_data(stock: Stock) -> tuple[str, dict[str, list[float] | list[int]] | None, str | None]:
    import random
    time.sleep(random.uniform(0.01, 0.04))
    symbol = f"{stock.symbol}.NS"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol, safe='.-')}?range=2y&interval=1d"
    try:
        request = Request(url, headers={"User-Agent": REQUEST_HEADERS["User-Agent"], "Accept": "application/json,*/*"})
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
            result = payload.get("chart", {}).get("result")
            if not result:
                return stock.symbol, None, "no chart result returned"
            data = result[0]
            parsed = parse_price_response(data)
            if not parsed:
                return stock.symbol, None, "failed to parse daily candle data"
            return stock.symbol, parsed, None
    except Exception as exc:
        return stock.symbol, None, str(exc)


def fetch_all_prices(universe: list[Stock], batch_size: int = 20) -> tuple[dict[str, dict[str, list[float] | list[int]]], list[dict[str, str]]]:
    import concurrent.futures
    all_prices: dict[str, dict[str, list[float] | list[int]]] = {}
    failures: list[dict[str, str]] = []

    print(f"Starting concurrent fetch of {len(universe)} charts using ThreadPoolExecutor...")
    t0 = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
        results = list(executor.map(fetch_chart_data, universe))

    for symbol, parsed_data, error_msg in results:
        if parsed_data:
            all_prices[symbol] = parsed_data
        else:
            failures.append({"symbol": symbol, "error": error_msg or "unknown error"})

    print(f"Finished concurrent fetch in {time.time() - t0:.2f} seconds. Success: {len(all_prices)}, Failures: {len(failures)}")
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


def average(values: list[int], count: int) -> float:
    sample = values[-count:]
    return sum(sample) / len(sample) if sample else 0


def signal_score(cross: dict, fast_period: int, slow_period: int) -> dict:
    score = 42
    reasons = []
    sessions_ago = cross["sessionsAgo"]
    close = float(cross["close"])
    fast = float(cross["fastEma"])
    slow = float(cross["slowEma"])
    volume = int(cross.get("volume", 0) or 0)
    average_volume = float(cross.get("averageVolume20", 0) or 0)
    spread_pct = abs(fast - slow) / close * 100 if close else 0

    if sessions_ago == 0:
        score += 24
        reasons.append("Fresh crossover in the latest daily candle")
    elif sessions_ago <= 5:
        score += 17
        reasons.append("Crossover happened within the last 5 sessions")
    else:
        score += 9
        reasons.append(f"Crossover is still inside the {SCAN_WINDOW_SESSIONS}-session window")

    if spread_pct >= 2:
        score += 14
        reasons.append("EMA spread is expanding strongly")
    elif spread_pct >= 1:
        score += 10
        reasons.append("EMA spread is meaningfully separated")
    elif spread_pct >= 0.35:
        score += 6
        reasons.append("EMA spread has started to separate")

    aligned = (
        close > fast > slow if cross["type"] == "bullish"
        else close < fast < slow
    )
    if aligned:
        score += 13
        reasons.append(f"Close confirms the {fast_period}/{slow_period} EMA direction")
    else:
        score += 5
        reasons.append("Close is near the moving-average zone")

    if average_volume and volume >= average_volume * 1.25:
        score += 12
        reasons.append("Volume is above the 20-session average")
    elif average_volume and volume >= average_volume:
        score += 7
        reasons.append("Volume is at or above its 20-session average")

    value = max(0, min(100, round(score)))
    if value >= 82:
        grade = "A"
    elif value >= 68:
        grade = "B"
    elif value >= 54:
        grade = "C"
    else:
        grade = "D"

    return {
        "value": value,
        "grade": grade,
        "emaSpreadPct": round(spread_pct, 2),
        "reasons": reasons[:4],
    }


def find_cross(closes: list[float], timestamps: list[int], volumes: list[int], fast_period: int, slow_period: int, window: int = SCAN_WINDOW_SESSIONS) -> dict | None:
    fast_ema = ema(closes, fast_period)
    slow_ema = ema(closes, slow_period)
    start = max(1, len(closes) - window)

    for index in range(start, len(closes)):
        if None in (fast_ema[index - 1], slow_ema[index - 1], fast_ema[index], slow_ema[index]):
            continue
        previous = float(fast_ema[index - 1]) - float(slow_ema[index - 1])
        current = float(fast_ema[index]) - float(slow_ema[index])
        cross_close = float(closes[index])
        latest_close = float(closes[-1])
        price_change = latest_close - cross_close
        price_change_pct = (price_change / cross_close * 100) if cross_close else 0
        latest_timestamp = timestamps[-1] if timestamps else None
        sparkline = [round(value, 2) for value in closes[max(0, index - 35) :]]
        if previous <= 0 and current > 0:
            cross = {
                "type": "bullish",
                "sessionsAgo": len(closes) - 1 - index,
                "fastEma": fast_ema[index],
                "slowEma": slow_ema[index],
                "latestFastEma": round(fast_ema[-1], 2) if fast_ema[-1] is not None else None,
                "latestSlowEma": round(slow_ema[-1], 2) if slow_ema[-1] is not None else None,
                "close": cross_close,
                "crossClose": cross_close,
                "latestClose": latest_close,
                "latestTimestamp": latest_timestamp,
                "priceChange": round(price_change, 2),
                "priceChangePct": round(price_change_pct, 2),
                "volume": volumes[index] if index < len(volumes) else 0,
                "averageVolume20": average(volumes[: index + 1], 20),
                "timestamp": timestamps[index],
                "sparkline": sparkline,
            }
            cross["score"] = signal_score(cross, fast_period, slow_period)
            return cross
        if previous >= 0 and current < 0:
            cross = {
                "type": "bearish",
                "sessionsAgo": len(closes) - 1 - index,
                "fastEma": fast_ema[index],
                "slowEma": slow_ema[index],
                "latestFastEma": round(fast_ema[-1], 2) if fast_ema[-1] is not None else None,
                "latestSlowEma": round(slow_ema[-1], 2) if slow_ema[-1] is not None else None,
                "close": cross_close,
                "crossClose": cross_close,
                "latestClose": latest_close,
                "latestTimestamp": latest_timestamp,
                "priceChange": round(price_change, 2),
                "priceChangePct": round(price_change_pct, 2),
                "volume": volumes[index] if index < len(volumes) else 0,
                "averageVolume20": average(volumes[: index + 1], 20),
                "timestamp": timestamps[index],
                "sparkline": sparkline,
            }
            cross["score"] = signal_score(cross, fast_period, slow_period)
            return cross
    return None


def stock_to_json(stock: Stock) -> dict[str, str]:
    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "marketCap": stock.market_cap,
        "sector": stock.sector,
        "isin": stock.isin,
    }


def build_scan_payload(
    scan_id: str,
    universe: list[Stock],
    price_data: dict[str, dict[str, list[float] | list[int]]],
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
        closes = candles.get("closes", [])
        timestamps = candles.get("timestamps", [])
        volumes = candles.get("volumes", [])
        if len(closes) < slow_period + SCAN_WINDOW_SESSIONS:
            skipped.append({"symbol": stock.symbol, "reason": f"needs at least {slow_period + SCAN_WINDOW_SESSIONS} daily candles"})
            continue
        cross = find_cross(closes, timestamps, volumes, fast_period, slow_period)
        if cross:
            results.append({**stock_to_json(stock), **cross})

    bucket_counts = {
        bucket: sum(1 for stock in universe if stock.market_cap == bucket)
        for bucket in ("large", "mid", "small", "other")
    }
    sector_counts = {}
    for stock in universe:
        sector_counts[stock.sector] = sector_counts.get(stock.sector, 0) + 1

    return {
        "market": "NSE India",
        "scanId": scan_id,
        "label": rule["label"],
        "rule": f"{fast_period} EMA / {slow_period} EMA crossover within last {SCAN_WINDOW_SESSIONS} daily sessions",
        "fastPeriod": fast_period,
        "slowPeriod": slow_period,
        "windowSessions": SCAN_WINDOW_SESSIONS,
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
        "sectorBuckets": dict(sorted(sector_counts.items())),
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
