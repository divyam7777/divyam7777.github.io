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
    ("RELIANCE", "Reliance Industries", "large"),
    ("TCS", "Tata Consultancy Services", "large"),
    ("HDFCBANK", "HDFC Bank", "large"),
    ("ICICIBANK", "ICICI Bank", "large"),
    ("INFY", "Infosys", "large"),
    ("BHARTIARTL", "Bharti Airtel", "large"),
    ("SBIN", "State Bank of India", "large"),
    ("ITC", "ITC", "large"),
    ("HINDUNILVR", "Hindustan Unilever", "large"),
    ("LT", "Larsen & Toubro", "large"),
    ("BAJFINANCE", "Bajaj Finance", "large"),
    ("HCLTECH", "HCL Technologies", "large"),
    ("KOTAKBANK", "Kotak Mahindra Bank", "large"),
    ("AXISBANK", "Axis Bank", "large"),
    ("ASIANPAINT", "Asian Paints", "large"),
    ("MARUTI", "Maruti Suzuki", "large"),
    ("SUNPHARMA", "Sun Pharma", "large"),
    ("TITAN", "Titan", "large"),
    ("ULTRACEMCO", "UltraTech Cement", "large"),
    ("NTPC", "NTPC", "large"),
    ("TATASTEEL", "Tata Steel", "large"),
    ("POWERGRID", "Power Grid", "large"),
    ("M&M", "Mahindra & Mahindra", "large"),
    ("NESTLEIND", "Nestle India", "large"),
    ("TECHM", "Tech Mahindra", "large"),
    ("ADANIENT", "Adani Enterprises", "large"),
    ("ADANIPORTS", "Adani Ports", "large"),
    ("WIPRO", "Wipro", "large"),
    ("ONGC", "ONGC", "large"),
    ("COALINDIA", "Coal India", "large"),
    ("ABB", "ABB India", "mid"),
    ("AUBANK", "AU Small Finance Bank", "mid"),
    ("ASTRAL", "Astral", "mid"),
    ("BALKRISIND", "Balkrishna Industries", "mid"),
    ("BANDHANBNK", "Bandhan Bank", "mid"),
    ("BANKBARODA", "Bank of Baroda", "mid"),
    ("BEL", "Bharat Electronics", "mid"),
    ("BHARATFORG", "Bharat Forge", "mid"),
    ("BHEL", "BHEL", "mid"),
    ("BIOCON", "Biocon", "mid"),
    ("CANBK", "Canara Bank", "mid"),
    ("CHOLAFIN", "Cholamandalam Investment", "mid"),
    ("CONCOR", "Container Corporation", "mid"),
    ("CUMMINSIND", "Cummins India", "mid"),
    ("DABUR", "Dabur", "mid"),
    ("FEDERALBNK", "Federal Bank", "mid"),
    ("GODREJCP", "Godrej Consumer Products", "mid"),
    ("HAVELLS", "Havells India", "mid"),
    ("IDFCFIRSTB", "IDFC First Bank", "mid"),
    ("INDHOTEL", "Indian Hotels", "mid"),
    ("IRCTC", "IRCTC", "mid"),
    ("JINDALSTEL", "Jindal Steel", "mid"),
    ("LUPIN", "Lupin", "mid"),
    ("MUTHOOTFIN", "Muthoot Finance", "mid"),
    ("NAUKRI", "Info Edge", "mid"),
    ("PERSISTENT", "Persistent Systems", "mid"),
    ("POLYCAB", "Polycab India", "mid"),
    ("RECLTD", "REC", "mid"),
    ("TVSMOTOR", "TVS Motor", "mid"),
    ("VBL", "Varun Beverages", "mid"),
    ("AARTIIND", "Aarti Industries", "small"),
    ("AFFLE", "Affle India", "small"),
    ("ANGELONE", "Angel One", "small"),
    ("APLAPOLLO", "APL Apollo Tubes", "small"),
    ("BATAINDIA", "Bata India", "small"),
    ("BLUESTARCO", "Blue Star", "small"),
    ("CDSL", "CDSL", "small"),
    ("CHAMBLFERT", "Chambal Fertilisers", "small"),
    ("DEEPAKNTR", "Deepak Nitrite", "small"),
    ("EIDPARRY", "EID Parry", "small"),
    ("EQUITASBNK", "Equitas Small Finance Bank", "small"),
    ("EXIDEIND", "Exide Industries", "small"),
    ("FINEORG", "Fine Organic Industries", "small"),
    ("GLENMARK", "Glenmark Pharma", "small"),
    ("GNFC", "GNFC", "small"),
    ("GRANULES", "Granules India", "small"),
    ("GUJGASLTD", "Gujarat Gas", "small"),
    ("HAPPSTMNDS", "Happiest Minds", "small"),
    ("IEX", "Indian Energy Exchange", "small"),
    ("INDIACEM", "India Cements", "small"),
    ("INTELLECT", "Intellect Design", "small"),
    ("KPITTECH", "KPIT Technologies", "small"),
    ("LALPATHLAB", "Dr Lal PathLabs", "small"),
    ("LAURUSLABS", "Laurus Labs", "small"),
    ("MANAPPURAM", "Manappuram Finance", "small"),
    ("METROPOLIS", "Metropolis Healthcare", "small"),
    ("NATIONALUM", "NALCO", "small"),
    ("PVRINOX", "PVR INOX", "small"),
    ("RBLBANK", "RBL Bank", "small"),
    ("TANLA", "Tanla Platforms", "small")
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

    for symbol, name, market_cap in NSE_UNIVERSE:
        try:
            closes, timestamps = fetch_yahoo(symbol)
            cross = find_cross(closes, timestamps)
            if cross:
                results.append({"symbol": symbol, "name": name, "marketCap": market_cap, **cross})
        except Exception as exc:
            failures.append({"symbol": symbol, "marketCap": market_cap, "error": str(exc)})
        time.sleep(0.08)

    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "market": "NSE India",
        "rule": "100 EMA / 200 EMA crossover within last 15 daily sessions",
        "generatedAt": generated_at,
        "universeSize": len(NSE_UNIVERSE),
        "universe": [{"symbol": symbol, "name": name, "marketCap": market_cap} for symbol, name, market_cap in NSE_UNIVERSE],
        "marketCapBuckets": {
            "large": sum(1 for _, _, cap in NSE_UNIVERSE if cap == "large"),
            "mid": sum(1 for _, _, cap in NSE_UNIVERSE if cap == "mid"),
            "small": sum(1 for _, _, cap in NSE_UNIVERSE if cap == "small")
        },
        "resultCount": len(results),
        "failureCount": len(failures),
        "results": sorted(results, key=lambda item: (item["sessionsAgo"], item["symbol"])),
        "failures": failures[:20]
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"generatedAt": generated_at, "results": len(results), "failures": len(failures)}, indent=2))


if __name__ == "__main__":
    main()
