from datetime import datetime, time as dt_time, timezone, timedelta

from config import SYMBOLS, MAX_OPEN_POSITIONS
from market import get_price
from strategy import moving_average_signal
from risk import can_trade, position_size, exit_signal
from paper_engine import load_state, open_trade, close_trade
from telegram import send_message

IST = timezone(timedelta(hours=5, minutes=30))


def market_open():
    now = datetime.now(IST)

    if now.weekday() >= 5:
        return False

    return dt_time(9, 15) <= now.time() <= dt_time(15, 30)


def run_cycle():
    state = load_state()

    result = {
        "time": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        "market_open": market_open(),
        "stocks": [],
        "events": [],
    }

    if state.get("status") == "paused":
        result["message"] = "ENGINE PAUSED"
        return result

    if not market_open():
        result["message"] = "MARKET CLOSED"
        return result

    buy_candidates = []

    for symbol in SYMBOLS:
        try:
            quote = get_price(symbol)

            if quote.get("stale"):
                result["stocks"].append({
                    "symbol": symbol,
                    "price": quote.get("price"),
                    "change_percent": quote.get("change_percent"),
                    "signal": "STALE",
                    "status": "STALE",
                })
                continue

            price = float(quote["price"])

            # Each stock has its own history.
            from multi_scanner import load_history, save_history

            history = load_history(symbol)
            timestamp = quote.get("timestamp")

            if history and history[-1].get("timestamp") == timestamp:
                signal = moving_average_signal(
                    [float(x["price"]) for x in history]
                )
            else:
                history.append({
                    "price": price,
                    "timestamp": timestamp,
                })
                save_history(symbol, history)

                signal = moving_average_signal(
                    [float(x["price"]) for x in history]
                )

            stock_result = {
                "symbol": symbol,
                "price": price,
                "change_percent": quote.get("change_percent", 0),
                "signal": signal,
                "ticks": len(history),
                "status": "OK",
            }

            trade = state["open_trades"].get(symbol)

            # Existing position
            if trade:
                exit_reason = exit_signal(trade, price)

                if exit_reason:
                    ok, closed = close_trade(
                        symbol,
                        price,
                        exit_reason
                    )

                    if ok:
                        msg = (
                            f"🔴 PAPER EXIT\n"
                            f"Symbol: {symbol}\n"
                            f"Exit: ₹{price:.2f}\n"
                            f"Qty: {closed['qty']}\n"
                            f"P&L: ₹{closed['pnl']:.2f}\n"
                            f"Reason: {exit_reason}"
                        )
                        send_message(msg)
                        result["events"].append(msg)

                elif signal == "SELL":
                    ok, closed = close_trade(
                        symbol,
                        price,
                        "SELL_SIGNAL"
                    )

                    if ok:
                        msg = (
                            f"🔴 PAPER SELL\n"
                            f"Symbol: {symbol}\n"
                            f"Exit: ₹{price:.2f}\n"
                            f"Qty: {closed['qty']}\n"
                            f"P&L: ₹{closed['pnl']:.2f}\n"
                            f"Signal: SELL"
                        )
                        send_message(msg)
                        result["events"].append(msg)

            # New BUY candidate
            elif (
                signal == "BUY"
                and can_trade(
                    state["capital"],
                    state["daily_pnl"]
                )
                and len(state["open_trades"]) < MAX_OPEN_POSITIONS
            ):
                short = sum(
                    [float(x["price"]) for x in history[-3:]]
                ) / 3

                long = sum(
                    [float(x["price"]) for x in history[-5:]]
                ) / 5

                strength = (
                    (short - long) / long
                    if long > 0 else 0
                )

                qty = position_size(
                    state["capital"],
                    price
                )

                if qty > 0:
                    buy_candidates.append({
                        "symbol": symbol,
                        "price": price,
                        "qty": qty,
                        "strength": strength,
                    })

            result["stocks"].append(stock_result)

        except Exception as e:
            result["stocks"].append({
                "symbol": symbol,
                "signal": "ERROR",
                "status": "ERROR",
                "error": str(e),
            })

    # Select strongest BUY only.
    if buy_candidates and len(state["open_trades"]) < MAX_OPEN_POSITIONS:
        best = max(
            buy_candidates,
            key=lambda x: x["strength"]
        )

        ok, trade = open_trade(
            best["symbol"],
            best["price"],
            best["qty"],
            "BUY"
        )

        if ok:
            msg = (
                f"🟢 PAPER BUY\n"
                f"Symbol: {best['symbol']}\n"
                f"Entry: ₹{best['price']:.2f}\n"
                f"Qty: {best['qty']}\n"
                f"Signal: BUY\n"
                f"Strength: {best['strength'] * 100:.3f}%"
            )

            send_message(msg)
            result["events"].append(msg)

    result["state"] = load_state()
    return result
