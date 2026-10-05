import os
import requests
import streamlit as st

st.set_page_config(
    page_title="Paper Trader",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Paper Trader")
st.caption("NSE • PAPER MODE")

API_URL = st.text_input(
    "Backend API URL",
    value=os.getenv("TRADING_API_URL", "http://127.0.0.1:8000"),
)

TOKEN = st.text_input(
    "API Token",
    value=os.getenv("TRADING_API_TOKEN", ""),
    type="password",
)

headers = {
    "Authorization": f"Bearer {TOKEN}"
}


def api_get(path):
    r = requests.get(
        f"{API_URL.rstrip('/')}{path}",
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def api_post(path):
    r = requests.post(
        f"{API_URL.rstrip('/')}{path}",
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


if st.button("🔄 Refresh"):
    st.rerun()

try:
    status = api_get("/status")
    quote = api_get("/quote")

    capital = status.get("capital", 0)
    available = status.get("available", 0)
    daily_pnl = status.get("daily_pnl", 0)
    trades = status.get("trades", [])
    open_trade = status.get("open_trade")
    engine_status = status.get("status", "unknown")

    st.success("🟢 Backend Connected")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Capital", f"₹{capital:,.2f}")
    c2.metric("Available", f"₹{available:,.2f}")
    c3.metric("Today's P&L", f"₹{daily_pnl:,.2f}")
    c4.metric("Total Trades", len(trades))

    st.divider()

    q1, q2, q3, q4 = st.columns(4)

    q1.metric("Symbol", quote.get("symbol", "-"))
    q2.metric("Price", f"₹{quote.get('price', 0):,.2f}")
    q3.metric("Change", f"{quote.get('change_percent', 0):+.2f}%")
    q4.metric("Engine", engine_status.upper())

    st.divider()

    st.subheader("⚙️ Controls")

    b1, b2 = st.columns(2)

    with b1:
        if st.button("⏸️ Pause Trading", use_container_width=True):
            result = api_post("/pause")
            st.success(result.get("status", "paused"))
            st.rerun()

    with b2:
        if st.button("▶️ Resume Trading", use_container_width=True):
            result = api_post("/resume")
            st.success(result.get("status", "running"))
            st.rerun()

    st.divider()

    st.subheader("📌 Open Trade")

    if open_trade:
        st.json(open_trade)
    else:
        st.info("No open trade")

    st.subheader("📊 Recent Trades")

    if trades:
        st.dataframe(
            trades[-20:],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No completed paper trades yet.")

except Exception as e:
    st.error(f"Backend connection failed: {e}")
    st.info(
        "Check API URL, API token, and make sure api.py is running."
    )
