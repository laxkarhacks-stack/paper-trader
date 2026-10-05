import json
from pathlib import Path
from datetime import datetime
from config import STARTING_CAPITAL, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT

STATE_FILE = Path(__file__).parent / "state.json"


def default_state():
    return {
        "capital": STARTING_CAPITAL,
        "available": STARTING_CAPITAL,
        "daily_pnl": 0,
        "daily_date": datetime.now().strftime("%Y-%m-%d"),
        "trades": [],
        "open_trades": {},
        "status": "running",
    }


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_state():
    if not STATE_FILE.exists():
        state = default_state()
        save_state(state)
        return state

    state = json.loads(STATE_FILE.read_text())

    # Old single-position format migration
    if "open_trades" not in state:
        old = state.get("open_trade")
        state["open_trades"] = {}

        if old:
            symbol = old.get("symbol", "RELIANCE")
            state["open_trades"][symbol] = old

        state.pop("open_trade", None)

    today = datetime.now().strftime("%Y-%m-%d")

    if state.get("daily_date") != today:
        state["daily_date"] = today
        state["daily_pnl"] = 0

    save_state(state)
    return state


def open_trade(symbol, price, qty, side="BUY"):
    state = load_state()

    if symbol in state["open_trades"]:
        return False, "Trade already open"

    price = float(price)
    qty = int(qty)

    if price <= 0 or qty <= 0:
        return False, "Invalid price or quantity"

    cost = round(price * qty, 2)

    if cost > state["available"]:
        return False, "Insufficient available capital"

    trade = {
        "symbol": symbol,
        "side": side,
        "entry": price,
        "qty": qty,
        "value": cost,
        "stop_loss": round(price * (1 - STOP_LOSS_PERCENT), 2),
        "take_profit": round(price * (1 + TAKE_PROFIT_PERCENT), 2),
        "time": datetime.now().isoformat(),
    }

    state["available"] = round(state["available"] - cost, 2)
    state["open_trades"][symbol] = trade

    save_state(state)
    return True, trade


def close_trade(symbol, price, reason="SIGNAL"):
    state = load_state()
    trade = state["open_trades"].get(symbol)

    if trade is None:
        return False, "No open trade"

    price = float(price)
    entry = float(trade["entry"])
    qty = int(trade["qty"])

    if trade["side"] == "BUY":
        pnl = (price - entry) * qty
    else:
        pnl = (entry - price) * qty

    pnl = round(pnl, 2)

    trade["exit"] = price
    trade["pnl"] = pnl
    trade["exit_reason"] = reason
    trade["exit_time"] = datetime.now().isoformat()

    state["capital"] = round(state["capital"] + pnl, 2)

    # Return original position value + P&L to available cash
    state["available"] = round(
        state["available"] + trade["value"] + pnl,
        2
    )

    state["daily_pnl"] = round(
        state["daily_pnl"] + pnl,
        2
    )

    state["trades"].append(trade)
    del state["open_trades"][symbol]

    save_state(state)
    return True, trade


def reset_account():
    state = default_state()
    save_state(state)
    return state
