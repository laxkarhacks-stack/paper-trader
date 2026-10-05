import os
import time
import requests

from paper_engine import load_state, save_state
from reports import daily_report

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None


def send_message(text):
    if not CHAT_ID:
        print(text)
        return

    requests.post(
        f"{API}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=15,
    )


def status_text():
    s = load_state()
    trade = s.get("open_trade")

    text = (
        "🤖 PAPER TRADER STATUS\n\n"
        f"💰 Capital: ₹{s['capital']:.2f}\n"
        f"💵 Available: ₹{s['available']:.2f}\n"
        f"📈 Daily P&L: ₹{s['daily_pnl']:.2f}\n"
        f"📊 Trades: {len(s.get('trades', []))}\n"
        f"⚙️ Status: {s.get('status', 'running')}"
    )

    if trade:
        text += (
            "\n\n🟢 OPEN TRADE\n"
            f"Side: {trade['side']}\n"
            f"Entry: ₹{trade['entry']:.2f}\n"
            f"Qty: {trade['qty']}"
        )
    else:
        text += "\n\n⚪ No open trade"

    return text


def trades_text():
    trades = load_state().get("trades", [])

    if not trades:
        return "📊 No completed paper trades yet."

    lines = ["📊 RECENT PAPER TRADES\n"]

    for t in trades[-10:]:
        emoji = "🟢" if t.get("pnl", 0) > 0 else "🔴"
        lines.append(
            f"{emoji} Entry ₹{t['entry']:.2f} → "
            f"Exit ₹{t['exit']:.2f} | "
            f"Qty {t['qty']} | P&L ₹{t['pnl']:.2f}"
        )

    return "\n".join(lines)


def handle_command(command):
    command = command.strip().lower().split("@")[0]

    if command == "/start":
        return (
            "🤖 PAPER TRADER ONLINE\n\n"
            "/status — current status\n"
            "/today — today's P&L\n"
            "/trades — recent trades\n"
            "/report — full report\n"
            "/pause — pause trading\n"
            "/resume — resume trading"
        )

    if command == "/status":
        return status_text()

    if command == "/today":
        return f"📈 TODAY P&L: ₹{load_state()['daily_pnl']:.2f}"

    if command == "/trades":
        return trades_text()

    if command == "/report":
        return daily_report()

    if command == "/pause":
        s = load_state()
        s["status"] = "paused"
        save_state(s)
        return "⏸️ PAPER TRADER PAUSED"

    if command == "/resume":
        s = load_state()
        s["status"] = "running"
        save_state(s)
        return "▶️ PAPER TRADER RESUMED"

    return "❓ Unknown command. Send /start"


def poll():
    offset = None
    print("📡 Telegram command listener started")

    while True:
        try:
            params = {"timeout": 1}

            if offset is not None:
                params["offset"] = offset

            r = requests.get(
                f"{API}/getUpdates",
                params=params,
                timeout=8,
            )

            data = r.json()

            if not data.get("ok"):
                print("⚠️ Telegram API error:", data)
                time.sleep(3)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = str(message.get("chat", {}).get("id", ""))

                if CHAT_ID and chat_id != str(CHAT_ID):
                    continue

                if text.startswith("/"):
                    reply = handle_command(text)
                    send_message(reply)
                    print(f"📩 {text} → replied")

            time.sleep(2)

        except KeyboardInterrupt:
            print("\n🛑 Telegram listener stopped")
            break

        except Exception as e:
            print(f"⚠️ Telegram listener error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    poll()
