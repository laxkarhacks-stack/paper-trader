from config import (
    MAX_DAILY_LOSS,
    MAX_RISK_PER_TRADE,
    MAX_POSITION_PERCENT,
    STOP_LOSS_PERCENT,
    TAKE_PROFIT_PERCENT,
)

def can_trade(capital, daily_pnl):
    if capital <= 0:
        return False

    max_loss = capital * MAX_DAILY_LOSS

    if daily_pnl <= -max_loss:
        print(f"🛑 DAILY LOSS LIMIT: ₹{daily_pnl:.2f}")
        return False

    return True


def position_size(capital, price):
    if capital <= 0 or price <= 0:
        return 0

    risk_amount = capital * MAX_RISK_PER_TRADE
    stop_distance = price * STOP_LOSS_PERCENT

    if stop_distance <= 0:
        return 0

    qty_by_risk = int(risk_amount / stop_distance)
    qty_by_position = int((capital * MAX_POSITION_PERCENT) / price)

    return max(0, min(qty_by_risk, qty_by_position))


def exit_signal(trade, price):
    if not trade or price <= 0:
        return None

    entry = float(trade["entry"])
    side = trade.get("side", "BUY")

    if side == "BUY":
        if price <= entry * (1 - STOP_LOSS_PERCENT):
            return "STOP_LOSS"

        if price >= entry * (1 + TAKE_PROFIT_PERCENT):
            return "TAKE_PROFIT"

    return None
