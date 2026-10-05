import json
import time
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

from market import get_price
from paper_engine import load_state, open_trade, close_trade
from strategy import moving_average_signal
from risk import can_trade, position_size
from config import SYMBOL, POLL_SECONDS

HISTORY_FILE = "price_history.json"
MAX_HISTORY = 100
IST = ZoneInfo("Asia/Kolkata")


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-MAX_HISTORY:], f, indent=2)


def market_open():
    now = datetime.now(IST)

    if now.weekday() >= 5:
        return False

    return dt_time(9, 15) <= now.time() <= dt_time(15, 30)


def main():
    print("🤖 NSE Paper Trader started")
    print(f"📌 Symbol: {SYMBOL}")
    print(f"⏱️ Poll: {POLL_SECONDS}s")
    print("💰 Mode: PAPER ONLY")
    print("🛡️ Stale-price trading: BLOCKED")
    print()

    prices = load_history()
    last_timestamp = None

    while True:
        try:
            state = load_state()

            if state.get("status") == "paused":
                print("⏸️ TRADING PAUSED")
                time.sleep(POLL_SECONDS)
                continue

            if not market_open():
                print(
                    f"[{datetime.now(IST).strftime('%H:%M:%S')}] "
                    "🌙 Market closed"
                )
                time.sleep(POLL_SECONDS)
                continue

            quote = get_price(SYMBOL)

            if quote.get("stale") is True:
                print(
                    f"[{datetime.now(IST).strftime('%H:%M:%S')}] "
                    "🛑 STALE NSE DATA — NO TRADE"
                )
                time.sleep(POLL_SECONDS)
                continue

            timestamp = quote.get("timestamp")

            if timestamp and timestamp == last_timestamp:
                print(
                    f"[{datetime.now(IST).strftime('%H:%M:%S')}] "
                    "⏸️ No new market tick"
                )
                time.sleep(POLL_SECONDS)
                continue

            last_timestamp = timestamp

            price = quote["price"]

            prices.append(price)
            prices = prices[-MAX_HISTORY:]
            save_history(prices)

            signal = moving_average_signal(prices)
            trade = state.get("open_trade")

            print(
                f"[{datetime.now(IST).strftime('%H:%M:%S')}] "
                f"{SYMBOL} ₹{price:.2f} | "
                f"{quote['change_percent']:+.2f}% | "
                f"History: {len(prices)} | "
                f"Signal: {signal}"
            )

            if trade is None and signal == "BUY":
                if can_trade(
                    state["capital"],
                    state["daily_pnl"]
                ):
                    qty = position_size(
                        state["capital"],
                        price
                    )

                    if qty > 0:
                        ok, result = open_trade(
                            price,
                            "BUY",
                            qty
                        )

                        if ok:
                            print(
                                f"🟢 PAPER BUY @ ₹{price:.2f} "
                                f"| Qty: {qty}"
                            )

            elif trade is not None and signal == "SELL":
                ok, result = close_trade(price)

                if ok:
                    print(
                        f"🔴 PAPER SELL @ ₹{price:.2f} "
                        f"| Qty: {result['qty']} "
                        f"| P&L ₹{result['pnl']:.2f}"
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
