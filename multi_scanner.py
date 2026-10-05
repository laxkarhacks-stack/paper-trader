import json
from pathlib import Path

from config import SYMBOLS
from market import get_price
from strategy import moving_average_signal

HISTORY_DIR = Path(__file__).parent / "histories"
HISTORY_DIR.mkdir(exist_ok=True)

MAX_HISTORY = 100


def history_file(symbol):
    return HISTORY_DIR / f"{symbol}.json"


def load_history(symbol):
    try:
        data = json.loads(history_file(symbol).read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_history(symbol, history):
    history_file(symbol).write_text(
        json.dumps(history[-MAX_HISTORY:], indent=2)
    )


def scan_stock(symbol):
    try:
        quote = get_price(symbol)

        if quote.get("stale"):
            return {
                "symbol": symbol,
                "status": "STALE",
                "signal": "HOLD",
                "price": quote.get("price"),
            }

        history = load_history(symbol)
        timestamp = quote.get("timestamp")

        if not history or history[-1].get("timestamp") != timestamp:
            history.append({
                "price": quote["price"],
                "timestamp": timestamp,
            })
            save_history(symbol, history)

        prices = [float(x["price"]) for x in history]
        signal = moving_average_signal(prices)

        return {
            "symbol": symbol,
            "status": "OK",
            "signal": signal,
            "price": quote["price"],
            "change_percent": quote["change_percent"],
            "ticks": len(prices),
            "timestamp": timestamp,
        }

    except Exception as e:
        return {
            "symbol": symbol,
            "status": "ERROR",
            "signal": "HOLD",
            "error": str(e),
        }


def scan_all():
    return [scan_stock(symbol) for symbol in SYMBOLS]


if __name__ == "__main__":
    results = scan_all()

    print("\n========== BANK NIFTY STOCK SCAN ==========")

    for r in results:
        if r["status"] == "OK":
            print(
                f'{r["symbol"]:12} '
                f'₹{r["price"]:.2f} '
                f'{r["change_percent"]:+.2f}% '
                f'{r["signal"]:4} '
                f'ticks={r["ticks"]}'
            )
        else:
            print(
                f'{r["symbol"]:12} '
                f'{r["status"]} '
                f'{r.get("error", "")}'
            )

    buys = [r["symbol"] for r in results if r["signal"] == "BUY"]

    print("------------------------------------------")
    print("BUY candidates:", buys or "None")
    print("==========================================")
