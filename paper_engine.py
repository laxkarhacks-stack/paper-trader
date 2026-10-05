import json
from pathlib import Path
from datetime import datetime

STATE_FILE = Path(__file__).parent / "state.json"

def load_state():
    state = json.loads(STATE_FILE.read_text())

    today = datetime.now().strftime("%Y-%m-%d")

    if state.get("daily_date") != today:
        state["daily_date"] = today
        state["daily_pnl"] = 0
        save_state(state)

    return state

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def open_trade(price, side="BUY", qty=1):
    state = load_state()
    if state["open_trade"] is not None:
        return False, "Trade already open"

    trade = {
        "side": side,
        "entry": price,
        "qty": qty,
        "time": datetime.now().isoformat()
    }
    state["open_trade"] = trade
    save_state(state)
    return True, trade

def close_trade(price):
    state = load_state()
    trade = state["open_trade"]

    if trade is None:
        return False, "No open trade"

    if trade["side"] == "BUY":
        pnl = (price - trade["entry"]) * trade["qty"]
    else:
        pnl = (trade["entry"] - price) * trade["qty"]

    trade["exit"] = price
    trade["pnl"] = round(pnl, 2)
    trade["exit_time"] = datetime.now().isoformat()

    state["capital"] = round(state["capital"] + pnl, 2)
    state["available"] = state["capital"]
    state["daily_pnl"] = round(state["daily_pnl"] + pnl, 2)
    state["trades"].append(trade)
    state["open_trade"] = None

    save_state(state)
    return True, trade
