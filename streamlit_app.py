import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta

from config import SYMBOLS, POLL_SECONDS
from engine import run_cycle, market_open
from paper_engine import load_state, reset_account

IST = timezone(timedelta(hours=5, minutes=30))

st.set_page_config(
    page_title="Bank Nifty Paper Trader",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Bank Nifty Paper Trader")

state = load_state()

# -------------------------
# Account
# -------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Capital", f"₹{state['capital']:,.2f}")
c2.metric("Available", f"₹{state['available']:,.2f}")
c3.metric("Daily P&L", f"₹{state['daily_pnl']:,.2f}")
c4.metric("Open Positions", len(state["open_trades"]))

st.divider()

# -------------------------
# Controls
# -------------------------
col1, col2, col3 = st.columns(3)

if col1.button("▶️ Run One Scan", use_container_width=True):
    result = run_cycle()
    st.session_state["last_result"] = result
    st.rerun()

if col2.button("🔄 Refresh", use_container_width=True):
    st.rerun()

if col3.button("♻️ Reset ₹2L Account", use_container_width=True):
    reset_account()
    st.session_state.pop("last_result", None)
    st.success("Account reset to ₹2,00,000")
    st.rerun()

st.caption(
    f"Market: {'🟢 OPEN' if market_open() else '🔴 CLOSED'}  |  "
    f"IST: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}"
)

# -------------------------
# Auto Engine
# -------------------------
auto = st.toggle(
    "🤖 Auto Engine",
    value=st.session_state.get("auto_engine", False)
)

st.session_state["auto_engine"] = auto

if auto:
    st.info(
        f"Auto Engine enabled — scanner runs every {POLL_SECONDS} seconds "
        "while this Streamlit session remains active."
    )

    @st.fragment(run_every=f"{POLL_SECONDS}s")
    def automatic_engine():
        result = run_cycle()
        st.session_state["last_result"] = result

        if result.get("message"):
            st.write(result["message"])

        if result.get("events"):
            for event in result["events"]:
                st.success(event)

    automatic_engine()

# -------------------------
# Last scan
# -------------------------
result = st.session_state.get("last_result")

if result:
    st.subheader("🔎 12-Stock Scanner")

    rows = []

    for stock in result.get("stocks", []):
        rows.append({
            "Symbol": stock.get("symbol"),
            "Price": stock.get("price"),
            "Change %": stock.get("change_percent"),
            "Signal": stock.get("signal"),
            "Ticks": stock.get("ticks", 0),
            "Status": stock.get("status"),
        })

    if rows:
        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    if result.get("events"):
        st.subheader("⚡ Engine Events")

        for event in result["events"]:
            st.code(event)

# -------------------------
# Open Positions
# -------------------------
st.subheader("📌 Open Positions")

state = load_state()

if state["open_trades"]:
    rows = []

    for symbol, trade in state["open_trades"].items():
        rows.append({
            "Symbol": symbol,
            "Entry": trade["entry"],
            "Qty": trade["qty"],
            "Value": trade["value"],
            "Stop Loss": trade["stop_loss"],
            "Take Profit": trade["take_profit"],
            "Time": trade["time"],
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No open paper positions.")

# -------------------------
# Trade History
# -------------------------
st.subheader("📜 Trade History")

if state["trades"]:
    rows = []

    for trade in reversed(state["trades"][-50:]):
        rows.append({
            "Symbol": trade.get("symbol"),
            "Entry": trade.get("entry"),
            "Exit": trade.get("exit"),
            "Qty": trade.get("qty"),
            "P&L": trade.get("pnl"),
            "Reason": trade.get("exit_reason"),
            "Entry Time": trade.get("time"),
            "Exit Time": trade.get("exit_time"),
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No completed trades yet.")

# -------------------------
# Watchlist
# -------------------------
with st.expander("🏦 Bank Nifty Universe"):
    st.write(", ".join(SYMBOLS))

st.divider()

st.caption(
    "Paper trading only • No real orders • NSE market data • "
    "Strategy: 3-period MA vs 5-period MA"
)
