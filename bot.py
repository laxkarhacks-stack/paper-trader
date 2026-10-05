import json
import time
from datetime import datetime

from market import get_price
from paper_engine import load_state, save_state, open_trade, close_trade
from strategy import moving_average_signal
from risk import can_trade, position_size
from config import SYMBOL, POLL_SECONDS

HISTORY_FILE = "price_history.json"
MAX_HISTORY = 100


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-MAX_HISTORY:], f, indent=2)


def main():
    print("🤖 NSE Paper Trader started")
    print(f"📌 Symbol: {SYMBOL}")
    print(f"⏱️ Poll: {POLL_SECONDS}s")
    print("💰 Mode: PAPER ONLY")
    print()

    prices = load_history()

    while True:
        try:
            state = load_state()

            if state.get("status") == "paused":
                print("⏸️ TRADING PAUSED")
                time.sleep(POLL_SECONDS)
                continue

            quote = get_price(SYMBOL)
            price = quote["price"]

            prices.append(price)
            prices = prices[-MAX_HISTORY:]
            save_history(prices)

            signal = moving_average_signal(prices)
            trade = state.get("open_trade")

            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"{SYMBOL} ₹{price:.2f} | "
                f"{quote['change_percent']:+.2f}% | "
                f"History: {len(prices)} | "
                f"Signal: {signal}"
            )

            if trade is None and signal == "BUY":
                if can_trade(state["capital"], state["daily_pnl"]):
                    open_trade(price, "BUY", position_size(state["capital"], price))
                    print(f"🟢 PAPER BUY @ ₹{price:.2f}")

            elif trade is not None and signal == "SELL":
                ok, trade = close_trade(price)
                if ok:
                    print(
                        f"🔴 PAPER SELL @ ₹{price:.2f} | "
                        f"Qty: {trade["qty"]} | "
                        f"P&L ₹{trade["pnl"]:.2f}"
                    )

            time.sleep(POLL_SECONDS)

        except KeyboardInterrupt:
            print("\n🛑 Paper Trader stopped")
            break

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
