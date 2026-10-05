import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from market import get_price
from paper_engine import load_state, save_state, open_trade, close_trade
from strategy import moving_average_signal
from risk import can_trade, position_size
from config import SYMBOL

st.set_page_config(
    page_title="Paper Trader",
    page_icon="📈",
    layout="wide",
)

IST = ZoneInfo("Asia/Kolkata")
HISTORY_FILE = Path(__file__).parent / "price_history.json"
MAX_HISTORY = 100


def load_history():
    try:
        data = json.loads(HISTORY_FILE.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_history(history):
    HISTORY_FILE.write_text(
        json.dumps(history[-MAX_HISTORY:], indent=2)
    )


def market_open():
    now = datetime.now(IST)

    if now.weekday() >= 5:
        return False

    current = now.hour * 60 + now.minute
    return 555 <= current <= 930


def run_cycle():
    state = load_state()

    if state.get("status") == "paused":
        return "⏸️ Engine paused", None, state

    if not market_open():
        return "🌙 NSE market closed", None, state

    quote = get_price(SYMBOL)

    if quote.get("stale") is True:
        return "🛑 Stale NSE data — NO TRADE", quote, state

    prices = load_history()

    timestamp = quote.get("timestamp")

    if timestamp and prices:
        last = prices[-1]
        last_timestamp = (
            last.get("timestamp")
            if isinstance(last, dict)
            else None
        )

        if timestamp == last_timestamp:
            return "⏸️ No new market tick", quote, state

    prices.append({
        "price": quote["price"],
        "timestamp": timestamp,
    })
    save_history(prices)

    numeric_prices = [
        float(x["price"]) if isinstance(x, dict) else float(x)
        for x in prices
    ]

    signal = moving_average_signal(numeric_prices)
    trade = state.get("open_trade")

    if trade is None and signal == "BUY":
        if can_trade(
            state["capital"],
            state["daily_pnl"],
        ):
            qty = position_size(
                state["capital"],
                quote["price"],
            )

            if qty > 0:
                ok, result = open_trade(
                    quote["price"],
                    "BUY",
                    qty,
                )

                if ok:
                    return (
                        f"🟢 PAPER BUY @ ₹{quote['price']:.2f} "
                        f"| Qty {qty}",
                        quote,
                        load_state(),
                    )

    elif trade is not None and signal == "SELL":
        ok, result = close_trade(quote["price"])

        if ok:
            return (
                f"🔴 PAPER SELL @ ₹{quote['price']:.2f} "
                f"| P&L ₹{result['pnl']:.2f}",
                quote,
                load_state(),
            )

    return (
        f"✅ Cycle complete • Signal: {signal}",
        quote,
        load_state(),
    )


st.title("📈 Paper Trader")
st.caption("NSE • PAPER MODE • Streamlit Python Backend")

state = load_state()

# Controls
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("⚡ Run One Cycle", use_container_width=True):
        try:
            message, quote, state = run_cycle()

            if message.startswith("🟢") or message.startswith("🔴"):
                st.success(message)
            elif message.startswith("🛑"):
                st.error(message)
            else:
                st.info(message)

            st.rerun()
        except Exception as e:
            st.error(f"Cycle error: {e}")

with c2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

with c3:
    if state.get("status") == "running":
        if st.button("⏸️ Pause", use_container_width=True):
            state["status"] = "paused"
            save_state(state)
            st.rerun()
    else:
        if st.button("▶️ Resume", use_container_width=True):
            state["status"] = "running"
            save_state(state)
            st.rerun()

with c4:
    st.metric("Engine", state.get("status", "running").upper())

st.divider()

# Market
try:
    quote = get_price(SYMBOL)

    prices = load_history()

    numeric_prices = [
        float(x["price"]) if isinstance(x, dict) else float(x)
        for x in prices
    ]

    signal = moving_average_signal(numeric_prices)

    a, b, c, d = st.columns(4)

    a.metric("Symbol", quote["symbol"])

    b.metric(
        "Price",
        f"₹{quote['price']:,.2f}",
    )

    c.metric(
        "Change",
        f"{quote['change_percent']:+.2f}%",
    )

    d.metric("Signal", signal)

    if quote.get("stale"):
        st.warning("⚠️ Cached/stale NSE quote — trading blocked")

    st.caption(
        f"Market data: {quote.get('timestamp', 'N/A')}"
    )

except Exception as e:
    st.error(f"NSE market data error: {e}")

st.divider()

# Account
st.subheader("💰 Account")

a, b, c, d = st.columns(4)

a.metric(
    "Capital",
    f"₹{state.get('capital', 0):,.2f}",
)

a2 = b.metric(
    "Available",
    f"₹{state.get('available', 0):,.2f}",
)

c.metric(
    "Today's P&L",
    f"₹{state.get('daily_pnl', 0):,.2f}",
)

d.metric(
    "Trades",
    len(state.get("trades", [])),
)

st.divider()

# Open trade
st.subheader("📌 Open Trade")

if state.get("open_trade"):
    st.json(state["open_trade"])
else:
    st.info("No open trade")

# Trades
st.subheader("📊 Recent Trades")

trades = state.get("trades", [])

if trades:
    st.dataframe(
        trades[-20:],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No completed trades yet.")

st.divider()

st.caption(
    "Paper trading only • No real orders are placed."
)
