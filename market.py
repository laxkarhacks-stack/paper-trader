import json
import requests

MCP_URL = "https://mcp.nseindia.in/cmmkt/mcp"

def _initialize():
    r = requests.post(
        MCP_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "paper-trader",
                    "version": "1.0"
                }
            }
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.headers.get("Mcp-Session-Id")

def _call_quote(session_id, symbol):
    r = requests.post(
        MCP_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Mcp-Session-Id": session_id,
        },
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "cm_get_stock_quote",
                "arguments": {"symbol": symbol}
            }
        },
        timeout=20,
    )
    r.raise_for_status()

    for line in r.text.splitlines():
        if line.startswith("data:"):
            payload = json.loads(line[5:].strip())
            if "error" in payload:
                raise RuntimeError(payload["error"])

            result = payload.get("result", {})

            if result.get("isError"):
                raise RuntimeError(
                    result.get("content", [{}])[0].get("text", "NSE MCP error")
                )

            content = result.get("content", [])
            if not content:
                raise RuntimeError("NSE MCP returned empty content")

            text = content[0].get("text", "")
            data = json.loads(text) if isinstance(text, str) else text

            # cm_get_stock_quote normally returns {"stock": {...}}
            # Keep a clear error if NSE returns another structure.
            stock = data.get("stock")
            if not stock:
                raise RuntimeError(
                    "Unexpected NSE response: " + json.dumps(data)[:1000]
                )

            return stock

    raise RuntimeError("NSE MCP returned no data")

def get_price(symbol="RELIANCE"):
    session = _initialize()
    stock = _call_quote(session, symbol)

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
    }

if __name__ == "__main__":
    print(json.dumps(get_price(), indent=2))
