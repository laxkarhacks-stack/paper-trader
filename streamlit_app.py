import streamlit as st
from market import get_price
from paper_engine import load_state, save_state
from strategy import moving_average_signal

st.set_page_config(page_title="Paper Trader", page_icon="📈", layout="wide")

st.title("📈 Paper Trader")
st.caption("NSE • PAPER MODE • Streamlit Python Backend")

state = load_state()

# Controls
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

with c2:
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

with c3:
    st.metric("Engine", state.get("status", "running").upper())

st.divider()

# Market
try:
    quote = get_price("RELIANCE")

    prices = []
    try:
        import json
        from pathlib import Path

        history_file = Path(__file__).parent / "price_history.json"

        if history_file.exists():
            data = json.loads(history_file.read_text())
            if isinstance(data, list):
                prices = [
                    float(x["price"]) if isinstance(x, dict) else float(x)
                    for x in data
                ]
    except Exception:
        prices = []

    signal = moving_average_signal(prices)

    a, b, c, d = st.columns(4)

    a.metric("Symbol", quote["symbol"])
    b.metric("Price", f"₹{quote['price']:,.2f}")
    c.metric("Change", f"{quote['change_percent']:+.2f}%")
    d.metric("Signal", signal)

    st.caption(f"Market data: {quote.get('timestamp', 'N/A')}")

except Exception as e:
    st.error(f"NSE market data error: {e}")

st.divider()

# Account
st.subheader("💰 Account")

a, b, c, d = st.columns(4)

a.metric("Capital", f"₹{state.get('capital', 0):,.2f}")
b.metric("Available", f"₹{state.get('available', 0):,.2f}")
c.metric("Today's P&L", f"₹{state.get('daily_pnl', 0):,.2f}")
d.metric("Trades", len(state.get("trades", [])))

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

st.caption("Paper trading only • No real orders are placed.")
