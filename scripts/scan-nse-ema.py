#!/usr/bin/env python3
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

NSE_UNIVERSE = [
    ("RELIANCE", "Reliance Industries"), ("TCS", "Tata Consultancy Services"), ("HDFCBANK", "HDFC Bank"),
    ("ICICIBANK", "ICICI Bank"), ("INFY", "Infosys"), ("BHARTIARTL", "Bharti Airtel"),
    ("SBIN", "State Bank of India"), ("ITC", "ITC"), ("HINDUNILVR", "Hindustan Unilever"),
    ("LT", "Larsen & Toubro"), ("BAJFINANCE", "Bajaj Finance"), ("HCLTECH", "HCL Technologies"),
    ("KOTAKBANK", "Kotak Mahindra Bank"), ("AXISBANK", "Axis Bank"), ("ASIANPAINT", "Asian Paints"),
    ("MARUTI", "Maruti Suzuki"), ("SUNPHARMA", "Sun Pharma"), ("TITAN", "Titan"),
    ("ULTRACEMCO", "UltraTech Cement"), ("NTPC", "NTPC"), ("TATASTEEL", "Tata Steel"),
    ("POWERGRID", "Power Grid"), ("M&M", "Mahindra & Mahindra"), ("NESTLEIND", "Nestle India"),
    ("TECHM", "Tech Mahindra"), ("ADANIENT", "Adani Enterprises"), ("ADANIPORTS", "Adani Ports"),
    ("WIPRO", "Wipro"), ("ONGC", "ONGC"), ("COALINDIA", "Coal India"),
    ("JSWSTEEL", "JSW Steel"), ("GRASIM", "Grasim"), ("HINDALCO", "Hindalco"),
    ("BAJAJFINSV", "Bajaj Finserv"), ("TATAMOTORS", "Tata Motors"), ("EICHERMOT", "Eicher Motors"),
    ("CIPLA", "Cipla"), ("DRREDDY", "Dr. Reddy's"), ("DIVISLAB", "Divi's Laboratories"),
    ("BRITANNIA", "Britannia"), ("HEROMOTOCO", "Hero MotoCorp"), ("BPCL", "BPCL"),
    ("APOLLOHOSP", "Apollo Hospitals"), ("SBILIFE", "SBI Life"), ("HDFCLIFE", "HDFC Life"),
    ("BAJAJ-AUTO", "Bajaj Auto"), ("TATACONSUM", "Tata Consumer"), ("INDUSINDBK", "IndusInd Bank")
]


def ema(values, period):
    output = [None] * len(values)
    if len(values) < period:
        return output
    seed = sum(values[:period]) / period
    output[period - 1] = seed
    multiplier = 2 / (period + 1)
    for index in range(period, len(values)):
        output[index] = (values[index] - output[index - 1]) * multiplier + output[index - 1]
    return output


def find_cross(closes, timestamps):
    ema100 = ema(closes, 100)
    ema200 = ema(closes, 200)
    start = max(1, len(closes) - 15)
    for index in range(start, len(closes)):
        if None in (ema100[index - 1], ema200[index - 1], ema100[index], ema200[index]):
            continue
        previous = ema100[index - 1] - ema200[index - 1]
        current = ema100[index] - ema200[index]
        if previous <= 0 and current > 0:
            return {
                "type": "bullish", "sessionsAgo": len(closes) - 1 - index,
                "ema100": ema100[index], "ema200": ema200[index], "close": closes[index],
                "timestamp": timestamps[index]
            }
        if previous >= 0 and current < 0:
            return {
                "type": "bearish", "sessionsAgo": len(closes) - 1 - index,
                "ema100": ema100[index], "ema200": ema200[index], "close": closes[index],
                "timestamp": timestamps[index]
            }
    return None


def fetch_yahoo(symbol):
    yahoo_symbol = quote(f"{symbol}.NS", safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range=2y&interval=1d"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=18) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload.get("chart", {}).get("result", [None])[0]
    if not result:
        raise RuntimeError("no chart result")
    quote_data = result.get("indicators", {}).get("quote", [None])[0]
    timestamps = result.get("timestamp") or []
    closes = (quote_data or {}).get("close") or []
    rows = [(float(close), int(timestamps[index])) for index, close in enumerate(closes) if close is not None and math.isfinite(float(close))]
    return [row[0] for row in rows], [row[1] for row in rows]


def main():
    output_path = Path("public/stocks/data/ema-crosses.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results = []
    failures = []

    for symbol, name in NSE_UNIVERSE:
        try:
            closes, timestamps = fetch_yahoo(symbol)
            cross = find_cross(closes, timestamps)
            if cross:
                results.append({"symbol": symbol, "name": name, **cross})
        except Exception as exc:
            failures.append({"symbol": symbol, "error": str(exc)})
        time.sleep(0.08)

    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "market": "NSE India",
        "rule": "100 EMA / 200 EMA crossover within last 15 daily sessions",
        "generatedAt": generated_at,
        "universeSize": len(NSE_UNIVERSE),
        "resultCount": len(results),
        "failureCount": len(failures),
        "results": sorted(results, key=lambda item: (item["sessionsAgo"], item["symbol"])),
        "failures": failures[:20]
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"generatedAt": generated_at, "results": len(results), "failures": len(failures)}, indent=2))


if __name__ == "__main__":
    main()
