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
    "50-200": {"fast": 50, "slow": 200, "label": "50 / 200 EMA cross"},
}
SCAN_WINDOW_SESSIONS = 60
RSI_PERIOD = 14
ADX_PERIOD = 14
MIN_RSI = 50
MAX_RSI = 70
MIN_ADX = 20
MIN_VOLUME_MULTIPLE = 1.5
MIN_AVERAGE_TURNOVER = 100_000_000
MAX_DISTANCE_FROM_FAST_EMA_PCT = 10
MARKET_TREND_SYMBOLS = [
    ("^NSEI", "Nifty 50"),
    ("NIFTYBEES.NS", "Nifty Bees"),
]
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
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8-sig", errors="replace")
        except Exception as e:
            if attempt == 2:
                print(f"Failed to fetch {url}: {e}")
                raise
            time.sleep(2)


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


def load_cached_universe(limit: int | None = None) -> list[Stock]:
    fallback_paths = [
        DEFAULT_OUTPUT_DIR / "ema-100-200-crosses.json",
        Path("data/ema-100-200-crosses.json"),
        Path("stocks/data/ema-100-200-crosses.json"),
    ]

    for path in fallback_paths:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            rows = payload.get("universe") or []
            stocks = []
            for row in rows:
                symbol = str(row.get("symbol", "")).upper().replace(".NS", "").strip()
                if not symbol:
                    continue
                stocks.append(
                    Stock(
                        symbol=symbol,
                        name=row.get("name", symbol),
                        market_cap=row.get("marketCap", "other"),
                        sector=row.get("sector", "Unclassified"),
                        isin=row.get("isin", ""),
                    )
                )
            if stocks:
                stocks = sorted(stocks, key=lambda stock: stock.symbol)
                print(f"Using cached NSE universe from {path} because the live NSE universe was unavailable.")
                return stocks[:limit] if limit else stocks
        except Exception as exc:
            print(f"Failed to read cached universe from {path}: {exc}")

    return []


def classify_symbol(symbol: str, market_metadata: dict[str, dict[str, str]]) -> str:
    return market_metadata.get(symbol, {}).get("marketCap", "other")


def sector_for_symbol(symbol: str, market_metadata: dict[str, dict[str, str]]) -> str:
    return market_metadata.get(symbol, {}).get("sector", "Unclassified")


def fetch_nse_universe(limit: int | None = None) -> list[Stock]:
    try:
        text = fetch_text(NSE_EQUITY_URL)
    except Exception:
        cached = load_cached_universe(limit=limit)
        if cached:
            return cached
        raise

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
    highs = quote_data.get("high") or []
    lows = quote_data.get("low") or []
    rows = []
    for index, close in enumerate(closes):
        if close is None or index >= len(timestamps):
            continue
        value = float(close)
        if math.isfinite(value):
            volume = volumes[index] if index < len(volumes) and volumes[index] is not None else 0
            high_val = float(highs[index]) if index < len(highs) and highs[index] is not None else value
            low_val = float(lows[index]) if index < len(lows) and lows[index] is not None else value
            rows.append((value, int(timestamps[index]), int(volume), high_val, low_val))
    if not rows:
        return None
    return {
        "closes": [row[0] for row in rows],
        "timestamps": [row[1] for row in rows],
        "volumes": [row[2] for row in rows],
        "highs": [row[3] for row in rows],
        "lows": [row[4] for row in rows],
    }


def yahoo_symbol_to_nse(raw_symbol: str) -> str:
    decoded = unquote(raw_symbol or "")
    return decoded[:-3].upper() if decoded.upper().endswith(".NS") else decoded.upper()


def fetch_yahoo_chart(symbol: str) -> tuple[dict[str, list[float] | list[int]] | None, str | None]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol, safe='.-^')}?range=2y&interval=1d"
    try:
        request = Request(url, headers={"User-Agent": REQUEST_HEADERS["User-Agent"], "Accept": "application/json,*/*"})
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
            result = payload.get("chart", {}).get("result")
            if not result:
                return None, "no chart result returned"
            parsed = parse_price_response(result[0])
            if not parsed:
                return None, "failed to parse daily candle data"
            return parsed, None
    except Exception as exc:
        return None, str(exc)


def fetch_chart_data(stock: Stock) -> tuple[str, dict[str, list[float] | list[int]] | None, str | None]:
    import random
    time.sleep(random.uniform(0.01, 0.04))
    symbol = f"{stock.symbol}.NS"
    parsed, error = fetch_yahoo_chart(symbol)
    return stock.symbol, parsed, error


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


def trailing_average(values: list[float] | list[int], end_index: int, count: int) -> float:
    if end_index < 0:
        return 0
    start = max(0, end_index - count + 1)
    sample = [float(value) for value in values[start : end_index + 1]]
    return sum(sample) / len(sample) if sample else 0


def rsi(values: list[float], period: int = RSI_PERIOD) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return output

    gains = [0.0] * len(values)
    losses = [0.0] * len(values)
    for index in range(1, len(values)):
        change = values[index] - values[index - 1]
        gains[index] = max(change, 0)
        losses[index] = max(-change, 0)

    average_gain = sum(gains[1 : period + 1]) / period
    average_loss = sum(losses[1 : period + 1]) / period
    output[period] = 100 if average_loss == 0 else 100 - (100 / (1 + average_gain / average_loss))

    for index in range(period + 1, len(values)):
        average_gain = ((average_gain * (period - 1)) + gains[index]) / period
        average_loss = ((average_loss * (period - 1)) + losses[index]) / period
        output[index] = 100 if average_loss == 0 else 100 - (100 / (1 + average_gain / average_loss))

    return output


def adx(highs: list[float], lows: list[float], closes: list[float], period: int = ADX_PERIOD) -> dict[str, list[float | None]]:
    length = min(len(highs), len(lows), len(closes))
    adx_values: list[float | None] = [None] * length
    plus_di_values: list[float | None] = [None] * length
    minus_di_values: list[float | None] = [None] * length

    if length <= period * 2:
        return {"adx": adx_values, "plusDi": plus_di_values, "minusDi": minus_di_values}

    true_ranges = [0.0] * length
    plus_dm = [0.0] * length
    minus_dm = [0.0] * length

    for index in range(1, length):
        high = float(highs[index])
        low = float(lows[index])
        previous_high = float(highs[index - 1])
        previous_low = float(lows[index - 1])
        previous_close = float(closes[index - 1])

        true_ranges[index] = max(high - low, abs(high - previous_close), abs(low - previous_close))
        up_move = high - previous_high
        down_move = previous_low - low
        plus_dm[index] = up_move if up_move > down_move and up_move > 0 else 0
        minus_dm[index] = down_move if down_move > up_move and down_move > 0 else 0

    smoothed_tr = sum(true_ranges[1 : period + 1])
    smoothed_plus_dm = sum(plus_dm[1 : period + 1])
    smoothed_minus_dm = sum(minus_dm[1 : period + 1])
    dx_values: list[float | None] = [None] * length

    for index in range(period, length):
        if index > period:
            smoothed_tr = smoothed_tr - (smoothed_tr / period) + true_ranges[index]
            smoothed_plus_dm = smoothed_plus_dm - (smoothed_plus_dm / period) + plus_dm[index]
            smoothed_minus_dm = smoothed_minus_dm - (smoothed_minus_dm / period) + minus_dm[index]

        plus_di = 100 * (smoothed_plus_dm / smoothed_tr) if smoothed_tr else 0
        minus_di = 100 * (smoothed_minus_dm / smoothed_tr) if smoothed_tr else 0
        plus_di_values[index] = plus_di
        minus_di_values[index] = minus_di
        denominator = plus_di + minus_di
        dx_values[index] = 100 * abs(plus_di - minus_di) / denominator if denominator else 0

        if index == period * 2:
            seed_values = [value for value in dx_values[period + 1 : index + 1] if value is not None]
            adx_values[index] = sum(seed_values) / len(seed_values) if seed_values else None
        elif index > period * 2 and adx_values[index - 1] is not None and dx_values[index] is not None:
            adx_values[index] = ((float(adx_values[index - 1]) * (period - 1)) + float(dx_values[index])) / period

    return {"adx": adx_values, "plusDi": plus_di_values, "minusDi": minus_di_values}


def build_market_trend() -> dict:
    for symbol, label in MARKET_TREND_SYMBOLS:
        candles, error = fetch_yahoo_chart(symbol)
        if not candles:
            continue
        closes = [float(value) for value in candles.get("closes", [])]
        timestamps = candles.get("timestamps", [])
        ema200 = ema(closes, 200)
        if not closes or not ema200 or ema200[-1] is None:
            continue
        latest_close = float(closes[-1])
        latest_ema200 = float(ema200[-1])
        return {
            "symbol": symbol,
            "label": label,
            "latestClose": round(latest_close, 2),
            "ema200": round(latest_ema200, 2),
            "timestamp": timestamps[-1] if timestamps else None,
            "isBullish": latest_close > latest_ema200,
            "filterApplied": True,
        }

    return {
        "symbol": None,
        "label": "Nifty 50",
        "latestClose": None,
        "ema200": None,
        "timestamp": None,
        "isBullish": None,
        "filterApplied": False,
        "warning": "Nifty trend data was unavailable, so the market trend gate could not be applied.",
    }


def quality_checks(cross: dict) -> dict:
    latest_close = float(cross.get("latestClose") or 0)
    latest_fast = float(cross.get("latestFastEma") or 0)
    latest_slow = float(cross.get("latestSlowEma") or 0)
    latest_volume = float(cross.get("latestVolume") or 0)
    cross_volume = float(cross.get("crossVolume") or 0)
    cross_average_volume = float(cross.get("crossAverageVolume20") or 0)
    average_volume = float(cross.get("averageVolume20") or 0)
    average_turnover = float(cross.get("averageTurnover20") or 0)
    latest_rsi = cross.get("rsi14")
    latest_adx = cross.get("adx14")
    plus_di = cross.get("plusDi14")
    minus_di = cross.get("minusDi14")
    distance_from_fast = cross.get("distanceFromFastEmaPct")
    fast_slope = cross.get("fastEmaSlopePct")

    checks = {
        "bullishSetup": cross.get("type") == "bullish",
        "priceAboveEmaStack": latest_close > latest_fast > latest_slow,
        "fastEmaSlopePositive": fast_slope is not None and float(fast_slope) > 0,
        "notOverextended": distance_from_fast is not None and float(distance_from_fast) <= MAX_DISTANCE_FROM_FAST_EMA_PCT,
        "volumeConfirmed": cross_average_volume > 0 and cross_volume >= cross_average_volume * MIN_VOLUME_MULTIPLE,
        "liquidTurnover": average_turnover >= MIN_AVERAGE_TURNOVER,
        "rsiHealthy": latest_rsi is not None and MIN_RSI <= float(latest_rsi) <= MAX_RSI,
        "diPlusAboveMinus": (
            plus_di is not None
            and minus_di is not None
            and float(plus_di) > float(minus_di)
        ),
        "diPlus3xMinus": (
            plus_di is not None
            and minus_di is not None
            and float(plus_di) >= 3 * float(minus_di)
        ),
        "adxSuperTrend": latest_adx is not None and float(latest_adx) >= 32,
        "rsiAdxRatio": latest_rsi is not None and latest_adx is not None and float(latest_rsi) >= float(latest_adx) * 1.7,
        "diPlusNearAdx": (
            plus_di is not None
            and latest_adx is not None
            and abs(float(plus_di) - float(latest_adx)) <= float(latest_adx) * 0.10
        ),
    }
    labels = {
        "bullishSetup": "Bullish EMA crossover",
        "priceAboveEmaStack": "Close is above EMA stack",
        "fastEmaSlopePositive": "EMA slope is positive",
        "notOverextended": f"Price is within {MAX_DISTANCE_FROM_FAST_EMA_PCT}% of fast EMA",
        "volumeConfirmed": f"Volume is at least {MIN_VOLUME_MULTIPLE}x 20-session average",
        "liquidTurnover": "20-session average turnover is at least Rs. 10 crore",
        "rsiHealthy": f"RSI {RSI_PERIOD} is between {MIN_RSI} and {MAX_RSI}",
        "diPlusAboveMinus": "+DI is above -DI",
        "diPlus3xMinus": "+DI is at least 3x -DI",
        "adxSuperTrend": "ADX is >= 32",
        "rsiAdxRatio": "RSI is >= 1.7x ADX",
        "diPlusNearAdx": "+DI is within ±10% of ADX",
    }
    failed = [labels[key] for key, passed in checks.items() if not passed]
    return {
        "passed": not failed,
        "checks": checks,
        "failed": failed,
    }


def signal_score(cross: dict, fast_period: int, slow_period: int) -> dict:
    score = 50
    reasons = []
    sessions_ago = cross["sessionsAgo"]
    close = float(cross["close"])
    fast = float(cross["fastEma"])
    slow = float(cross["slowEma"])
    volume = int(cross.get("latestVolume", cross.get("volume", 0)) or 0)
    average_volume = float(cross.get("averageVolume20", 0) or 0)
    average_turnover = float(cross.get("averageTurnover20", 0) or 0)
    rsi_value = cross.get("rsi14")
    adx_value = cross.get("adx14")
    distance_from_fast = cross.get("distanceFromFastEmaPct")
    spread_pct = abs(fast - slow) / close * 100 if close else 0

    if sessions_ago == 0:
        score += 15
        reasons.append("Fresh crossover in the latest daily candle")
    elif sessions_ago <= 5:
        score += 10
        reasons.append("Crossover happened within the last 5 sessions")
    else:
        score += 5
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
        score += 8
        reasons.append(f"Close confirms the {fast_period}/{slow_period} EMA direction")
    else:
        score += 2
        reasons.append("Close is near the moving-average zone")

    if average_volume:
        volume_multiple = volume / average_volume
        if volume_multiple >= 2:
            score += 12
            reasons.append("Latest volume is at least 2x the 20-session average")
        elif volume_multiple >= MIN_VOLUME_MULTIPLE:
            score += 8
            reasons.append("Latest volume confirms the breakout")

    if average_turnover >= MIN_AVERAGE_TURNOVER * 5:
        score += 8
        reasons.append("High liquidity with Rs. 50 crore plus average turnover")
    elif average_turnover >= MIN_AVERAGE_TURNOVER:
        score += 5
        reasons.append("Liquidity passes the Rs. 10 crore turnover filter")

    if rsi_value is not None:
        rsi_float = float(rsi_value)
        if 55 <= rsi_float <= 65:
            score += 10
            reasons.append("RSI is in a strong but not overheated zone")
        elif MIN_RSI <= rsi_float <= MAX_RSI:
            score += 6
            reasons.append("RSI confirms bullish momentum without overextension")

    if adx_value is not None:
        adx_float = float(adx_value)
        if adx_float >= 30:
            score += 10
            reasons.append("ADX shows a strong trend")
        elif adx_float > MIN_ADX:
            score += 6
            reasons.append("ADX confirms trend strength")

    if distance_from_fast is not None:
        distance = float(distance_from_fast)
        if distance <= 3:
            score += 8
            reasons.append("Price is still close to the fast EMA")
        elif distance <= 6:
            score += 5
            reasons.append("Price is not too far above the fast EMA")
        elif distance <= MAX_DISTANCE_FROM_FAST_EMA_PCT:
            score += 2
            reasons.append("Price is below the overextension limit")

    if cross.get("marketTrendConfirmed"):
        score += 5
        reasons.append("Nifty 50 is above its 200 EMA")

    value = max(0, min(100, round(score)))
    if value >= 85:
        grade = "A"
    elif value >= 75:
        grade = "B"
    elif value >= 60:
        grade = "C"
    else:
        grade = "D"

    return {
        "value": value,
        "grade": grade,
        "emaSpreadPct": round(spread_pct, 2),
        "reasons": reasons[:6],
    }


def find_cross(
    closes: list[float],
    timestamps: list[int],
    volumes: list[int],
    highs: list[float],
    lows: list[float],
    fast_period: int,
    slow_period: int,
    market_trend: dict,
    window: int = SCAN_WINDOW_SESSIONS,
) -> dict | None:
    fast_ema = ema(closes, fast_period)
    slow_ema = ema(closes, slow_period)
    rsi_values = rsi(closes)
    adx_values = adx(highs, lows, closes)
    start = max(1, len(closes) - window)
    latest_index = len(closes) - 1
    latest_fast = fast_ema[latest_index]
    latest_slow = slow_ema[latest_index]

    if latest_fast is None or latest_slow is None:
        return None
        
    if latest_fast <= latest_slow:
        return None

    for index in range(len(closes) - 1, start - 1, -1):
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
            if index < len(highs):
                high_slice = highs[index:]
                high_after_cross = max(high_slice)
                high_days_after_cross = high_slice.index(high_after_cross)
            else:
                high_after_cross = cross_close
                high_days_after_cross = 0
            
            high_after_cross_pct = ((high_after_cross - cross_close) / cross_close * 100) if cross_close else 0
            latest_volume = volumes[latest_index] if latest_index < len(volumes) else 0
            cross_volume = volumes[index] if index < len(volumes) else 0
            cross_average_volume_20 = trailing_average(volumes, index, 20)
            average_volume_20 = average(volumes, 20)
            average_turnover_20 = trailing_average(
                [float(close) * int(volumes[idx] if idx < len(volumes) else 0) for idx, close in enumerate(closes)],
                index,
                20,
            )
            fast_slope_pct = None
            if fast_ema[index - 1] is not None and fast_ema[index - 1]:
                fast_slope_pct = (float(fast_ema[index]) - float(fast_ema[index - 1])) / float(fast_ema[index - 1]) * 100
            cross_fast = float(fast_ema[index]) if fast_ema[index] is not None else None
            distance_from_fast = ((cross_close - cross_fast) / cross_fast * 100) if cross_fast else None
            market_confirmed = market_trend.get("isBullish") is True if market_trend.get("filterApplied") else True
            cross = {
                "type": "bullish",
                "sessionsAgo": len(closes) - 1 - index,
                "fastEma": fast_ema[index],
                "slowEma": slow_ema[index],
                "latestFastEma": round(float(latest_fast), 2),
                "latestSlowEma": round(float(latest_slow), 2),
                "close": cross_close,
                "crossClose": cross_close,
                "highAfterCross": round(high_after_cross, 2),
                "highAfterCrossPct": round(high_after_cross_pct, 2),
                "highDaysAfterCross": high_days_after_cross,
                "latestClose": latest_close,
                "latestTimestamp": latest_timestamp,
                "priceChange": round(price_change, 2),
                "priceChangePct": round(price_change_pct, 2),
                "volume": latest_volume,
                "crossVolume": cross_volume,
                "latestVolume": latest_volume,
                "crossAverageVolume20": round(cross_average_volume_20, 2),
                "averageVolume20": round(average_volume_20, 2),
                "volumeMultiple": round(cross_volume / cross_average_volume_20, 2) if cross_average_volume_20 else 0,
                "averageTurnover20": round(average_turnover_20, 2),
                "averageTurnover20Crore": round(average_turnover_20 / 10_000_000, 2),
                "rsi14": round(float(rsi_values[index]), 2) if rsi_values[index] is not None else None,
                "adx14": round(float(adx_values["adx"][index]), 2) if adx_values["adx"][index] is not None else None,
                "plusDi14": round(float(adx_values["plusDi"][index]), 2) if adx_values["plusDi"][index] is not None else None,
                "minusDi14": round(float(adx_values["minusDi"][index]), 2) if adx_values["minusDi"][index] is not None else None,
                "distanceFromFastEmaPct": round(distance_from_fast, 2) if distance_from_fast is not None else None,
                "fastEmaSlopePct": round(fast_slope_pct, 3) if fast_slope_pct is not None else None,
                "marketTrendConfirmed": market_confirmed,
                "timestamp": timestamps[index],
                "sparkline": sparkline,
            }
            cross["quality"] = quality_checks(cross)
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
    market_trend: dict,
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
        highs = candles.get("highs", [])
        lows = candles.get("lows", [])
        if len(closes) < slow_period + SCAN_WINDOW_SESSIONS:
            skipped.append({"symbol": stock.symbol, "reason": f"needs at least {slow_period + SCAN_WINDOW_SESSIONS} daily candles"})
            continue
        cross = find_cross(closes, timestamps, volumes, highs, lows, fast_period, slow_period, market_trend)
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
        "rule": f"Bullish {fast_period} EMA / {slow_period} EMA crossover within last {SCAN_WINDOW_SESSIONS} daily sessions with RSI, ADX, volume, turnover, extension, and Nifty trend filters",
        "fastPeriod": fast_period,
        "slowPeriod": slow_period,
        "windowSessions": SCAN_WINDOW_SESSIONS,
        "filters": {
            "direction": "bullish only",
            "priceStack": f"latest close > EMA {fast_period} > EMA {slow_period}",
            "maxDistanceFromFastEmaPct": MAX_DISTANCE_FROM_FAST_EMA_PCT,
            "volumeMultiple": MIN_VOLUME_MULTIPLE,
            "minimumAverageTurnover": MIN_AVERAGE_TURNOVER,
            "rsi": {"period": RSI_PERIOD, "min": MIN_RSI, "max": MAX_RSI},
            "adx": {"period": ADX_PERIOD, "min": MIN_ADX, "requiresPlusDiAboveMinusDi": True},
            "marketTrend": "Nifty 50 close > Nifty 50 EMA 200 when index data is available",
        },
        "marketTrend": market_trend,
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
    market_trend = build_market_trend()
    prices, failures = fetch_all_prices(universe)

    manifest = {
        "market": "NSE India",
        "generatedAt": generated_at,
        "universeSize": len(universe),
        "pricedUniverseSize": len(prices),
        "failureCount": len(failures),
        "marketTrend": market_trend,
        "availableScans": [],
    }

    for scan_id in SCAN_RULES:
        payload = build_scan_payload(scan_id, universe, prices, failures, generated_at, market_trend)
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

    write_json(output_dir / "scan-manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
