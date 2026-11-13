#!/usr/bin/env python3
"""Daily closing prices for the ledger's investment holdings.

Reads every ticker from Firestore (ledgers/shared-ledger/meta/assets), fetches the
last *closed* trading day's price from Yahoo Finance, and writes them back to the
same document under `prices`, which the app reads.

Runs on GitHub Actions (see .github/workflows/update-prices.yml). Standard library only.

Env:
  FIREBASE_PROJECT_ID  required, e.g. my-project-123
  FIREBASE_API_KEY     optional, the web apiKey from the app's Firebase config
  DRY_RUN=1            fetch and print prices without writing to Firestore
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

PROJECT = os.environ.get("FIREBASE_PROJECT_ID", "").strip()
API_KEY = os.environ.get("FIREBASE_API_KEY", "").strip()
DRY = os.environ.get("DRY_RUN") == "1"
DOC = "ledgers/shared-ledger/meta/assets"
CASH = {"AUD", "HKD", "USD", "JPY", "NTD", "TWD", "CNY", "GBP", "EUR", "SGD", "NZD", "CAD", "CHF", "KRW", "MYR", "THB"}
UA = {"User-Agent": "Mozilla/5.0 (ledger price updater)"}


def http(url, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = dict(UA)
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def doc_url(params=""):
    base = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents/{DOC}"
    q = []
    if API_KEY:
        q.append("key=" + urllib.parse.quote(API_KEY))
    if params:
        q.append(params)
    return base + ("?" + "&".join(q) if q else "")


def from_fs(v):
    """Firestore REST value -> plain Python."""
    if "mapValue" in v:
        return {k: from_fs(x) for k, x in v["mapValue"].get("fields", {}).items()}
    if "arrayValue" in v:
        return [from_fs(x) for x in v["arrayValue"].get("values", [])]
    for k in ("stringValue", "booleanValue", "timestampValue"):
        if k in v:
            return v[k]
    if "integerValue" in v:
        return int(v["integerValue"])
    if "doubleValue" in v:
        return float(v["doubleValue"])
    return None


def to_fs(x):
    if isinstance(x, bool):
        return {"booleanValue": x}
    if isinstance(x, int):
        return {"integerValue": str(x)}
    if isinstance(x, float):
        return {"doubleValue": x}
    if isinstance(x, dict):
        return {"mapValue": {"fields": {k: to_fs(v) for k, v in x.items()}}}
    if x is None:
        return {"nullValue": None}
    return {"stringValue": str(x)}


def norm(sym):
    s = str(sym or "").strip().upper()
    # US share classes: BRK.B -> BRK-B (Yahoo format); exchange suffixes like .AX are kept
    if "." in s:
        head, tail = s.rsplit(".", 1)
        if tail in ("A", "B", "C") and head.isalpha() and len(head) <= 5:
            s = f"{head}-{tail}"
    return s


def tickers(doc):
    out = set()
    for items in (doc.get("people") or {}).values():
        for a in items or []:
            for h in a.get("holdings") or []:
                s = norm(h.get("symbol") or h.get("name"))
                if s and s not in CASH:  # currency codes are cash, valued with FX in the app
                    out.add(s)
    return sorted(out)


def last_close(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=5d&interval=1d"
    r = http(url)["chart"]["result"][0]
    m, ts = r["meta"], r.get("timestamp") or []
    closes = (r.get("indicators", {}).get("quote") or [{}])[0].get("close") or []
    idx = next((i for i in range(len(ts) - 1, -1, -1) if closes[i]), -1)
    reg = (m.get("currentTradingPeriod") or {}).get("regular") or {}
    now = time.time()
    # today's session still open -> use the previous completed day
    if idx >= 0 and reg and now < reg.get("end", 0) and ts[idx] >= reg.get("start", 0):
        idx = next((i for i in range(idx - 1, -1, -1) if closes[i]), -1)
    price = float(closes[idx]) if idx >= 0 else float(m.get("chartPreviousClose") or 0)
    tz = m.get("exchangeTimezoneName") or "UTC"
    # crypto trades 24/7: today's open is yesterday's close (Yahoo sometimes leaves yesterday's bar empty)
    opens = (r.get("indicators", {}).get("quote") or [{}])[0].get("open") or []
    if m.get("instrumentType") == "CRYPTOCURRENCY" and ts and reg and ts[-1] >= reg.get("start", 0) and opens and opens[-1]:
        price = float(opens[-1])
        idx = len(ts) - 1
        crypto_date = (dt.datetime.fromtimestamp(ts[-1], ZoneInfo(tz)).date() - dt.timedelta(days=1)).isoformat()
    else:
        crypto_date = None
    if price <= 0:
        raise ValueError("no close")
    cur = m.get("currency") or "USD"
    if cur in ("GBp", "GBX"):
        price, cur = price / 100, "GBP"
    close_date = crypto_date or (dt.datetime.fromtimestamp(ts[idx], ZoneInfo(tz)).date().isoformat() if idx >= 0 else "")
    return {
        "price": round(price, 6),
        "currency": cur.upper(),
        "name": m.get("longName") or m.get("shortName") or sym,
        "closeDate": close_date,
        "at": int(now * 1000),
        "src": "github-yahoo",
    }


def main():
    if not PROJECT:
        sys.exit("FIREBASE_PROJECT_ID is not set")
    raw = http(doc_url())
    doc = from_fs({"mapValue": {"fields": raw.get("fields", {})}})
    syms = tickers(doc)
    print(f"{len(syms)} ticker(s): {', '.join(syms) or '-'}")
    prices, failed = {}, []
    for s in syms:
        try:
            prices[s] = last_close(s)
            q = prices[s]
            print(f"  {s:10} {q['currency']} {q['price']:.4f}  close {q['closeDate']}  {q['name']}")
        except Exception as e:  # keep going; the app keeps the previous price
            failed.append(s)
            print(f"  {s:10} FAILED: {e}")
        time.sleep(0.5)
    if not prices:
        print("Nothing to write")
        return 1 if failed else 0
    if DRY:
        print("DRY_RUN: not writing")
        return 0
    # update only prices.<ticker> fields so people's assets are never touched
    mask = "&".join("updateMask.fieldPaths=" + urllib.parse.quote(f"prices.`{s}`") for s in prices)
    mask += "&updateMask.fieldPaths=pricesAt"
    body = {"fields": {"prices": to_fs(prices), "pricesAt": to_fs(int(time.time() * 1000))}}
    http(doc_url(mask), method="PATCH", body=body)
    print(f"Wrote {len(prices)} price(s)" + (f"; failed: {', '.join(failed)}" if failed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
