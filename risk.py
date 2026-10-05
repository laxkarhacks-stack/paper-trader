from config import MAX_DAILY_LOSS, MAX_RISK_PER_TRADE


def can_trade(capital, daily_pnl):
    if capital <= 0:
        return False

    max_loss = capital * MAX_DAILY_LOSS

    if daily_pnl <= -max_loss:
        print(
            f"🛑 DAILY LOSS LIMIT HIT: "
            f"₹{daily_pnl:.2f} / -₹{max_loss:.2f}"
        )
        return False

    return True


def position_size(capital, price):
    if price <= 0:
        return 0

    risk_amount = capital * MAX_RISK_PER_TRADE
    qty = int(risk_amount / price)

    return max(1, qty)
