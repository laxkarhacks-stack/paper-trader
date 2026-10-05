import threading
import time
from datetime import datetime

import bot
import telegram

def run_trader():
    bot.main()

def run_telegram():
    telegram.poll()

def daily_report_scheduler():
    sent_date = None

    while True:
        try:
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")

            if now.hour == 23 and now.minute == 30 and sent_date != today:
                report = telegram.daily_report()
                telegram.send_message(
                    "🌙 11:30 PM DAILY REPORT\n\n" + report
                )
                print("📊 11:30 PM daily report sent")
                sent_date = today

            time.sleep(20)

        except Exception as e:
            print(f"⚠️ Report scheduler error: {e}")
            time.sleep(30)

print("🚀 PAPER TRADER SYSTEM STARTING")
print("📈 Trading engine: ON")
print("📩 Telegram control: ON")
print("📊 Daily report: 23:30")
print("💰 Mode: PAPER ONLY")

trader = threading.Thread(target=run_trader, daemon=True)
tg = threading.Thread(target=run_telegram, daemon=True)
reporter = threading.Thread(target=daily_report_scheduler, daemon=True)

trader.start()
tg.start()
reporter.start()

try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    print("\n🛑 PAPER TRADER SYSTEM STOPPED")
