from datetime import datetime
from paper_engine import load_state


def daily_report():
    state = load_state()
    today = state.get("daily_date")
    all_trades = state.get("trades", [])

    trades = [
        t for t in all_trades
        if str(t.get("exit_time", "")).startswith(str(today))
    ]

    wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
    losses = sum(1 for t in trades if t.get("pnl", 0) < 0)
    pnl = round(sum(t.get("pnl", 0) for t in trades), 2)

    win_rate = (wins / len(trades) * 100) if trades else 0

    return (
        "📊 DAILY PAPER REPORT\n\n"
        f"📅 Date: {today}\n"
        f"💰 Capital: ₹{state['capital']:.2f}\n"
        f"📈 Today's P&L: ₹{pnl:.2f}\n"
        f"📊 Today's Trades: {len(trades)}\n"
        f"🟢 Wins: {wins}\n"
        f"🔴 Losses: {losses}\n"
        f"🎯 Win Rate: {win_rate:.1f}%\n"
        f"🤖 Status: {state.get('status', 'running')}\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


if __name__ == "__main__":
    print(daily_report())
