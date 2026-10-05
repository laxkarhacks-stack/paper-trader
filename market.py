import json
import time
from pathlib import Path

import requests

MCP_URL = "https://mcp.nseindia.in/cmmkt/mcp"
CACHE_FILE = Path(__file__).parent / "quote_cache.json"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

TIMEOUT = 20
RETRIES = 3


def _post(payload, session_id=None):
    headers = HEADERS.copy()

    if session_id:
        headers["Mcp-Session-Id"] = session_id

    last_error = None

    for attempt in range(RETRIES):
        try:
            r = requests.post(
                MCP_URL,
                headers=headers,
                json=payload,
                timeout=TIMEOUT,
            )

            if r.status_code in (502, 503, 504):
                last_error = RuntimeError(
                    f"NSE gateway error: HTTP {r.status_code}"
                )

                if attempt < RETRIES - 1:
                    time.sleep(2 * (attempt + 1))
                    continue

                raise last_error

            r.raise_for_status()
            return r

        except (requests.RequestException, RuntimeError) as e:
            last_error = e

            if attempt < RETRIES - 1:
                time.sleep(2 * (attempt + 1))
            else:
                raise

    raise last_error


def _initialize():
    r = _post({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "paper-trader",
                "version": "1.0",
            },
        },
    })

    return r.headers.get("Mcp-Session-Id")


def _call_quote(session_id, symbol):
    r = _post(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "cm_get_stock_quote",
                "arguments": {"symbol": symbol},
            },
        },
        session_id=session_id,
    )

    for line in r.text.splitlines():
        if not line.startswith("data:"):
            continue

        payload = json.loads(line[5:].strip())

        if "error" in payload:
            raise RuntimeError(payload["error"])

        result = payload.get("result", {})

        if result.get("isError"):
            raise RuntimeError(
                result.get("content", [{}])[0].get(
                    "text",
                    "NSE MCP error",
                )
            )

        content = result.get("content", [])

        if not content:
            raise RuntimeError("NSE MCP returned empty content")

        text = content[0].get("text", "")
        data = json.loads(text) if isinstance(text, str) else text

        stock = data.get("stock")

        if not stock:
            raise RuntimeError(
                "Unexpected NSE response: "
                + json.dumps(data)[:1000]
            )

        return stock

    raise RuntimeError("NSE MCP returned no data")


def _format_quote(stock):
    return {
        "symbol": stock["symbol"],
        "price": float(stock["lastTradedPrice"]),
        "open": float(stock["openPrice"]),
        "high": float(stock["highPrice"]),
        "low": float(stock["lowPrice"]),
        "change": float(stock["change"]),
        "change_percent": float(stock["perChange"]),
        "volume": int(stock["volume"]),
        "timestamp": stock.get("latestTimestamp"),
        "source": "NSE",
        "stale": False,
    }


def _load_cache(symbol):
    try:
        if not CACHE_FILE.exists():
            return None

        data = json.loads(CACHE_FILE.read_text())

        if data.get("symbol") != symbol:
            return None

        data["stale"] = True
        data["source"] = "NSE cache"

        return data

    except Exception:
        return None


def _save_cache(quote):
    try:
        CACHE_FILE.write_text(
            json.dumps(quote, indent=2)
        )
    except Exception:
        pass


def get_price(symbol="RELIANCE"):
    try:
        session = _initialize()
        stock = _call_quote(session, symbol)

        quote = _format_quote(stock)
        _save_cache(quote)

        return quote

    except Exception as error:
        cached = _load_cache(symbol)

        if cached:
            cached["error"] = str(error)
            return cached

        raise RuntimeError(
            f"NSE unavailable and no cached quote: {error}"
        )


if __name__ == "__main__":
    print(json.dumps(get_price(), indent=2))
