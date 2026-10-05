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
    if capital <= 0 or price <= 0:
        return 0

    risk_amount = capital * MAX_RISK_PER_TRADE

    # Paper engine currently has no stop-loss distance,
    # so cap position by available capital instead of
    # pretending risk_amount is a true stop-loss risk.
    qty_by_capital = int(capital / price)

    if qty_by_capital <= 0:
        return 0

    # Never use more than 20% of capital in one position.
    max_position_value = capital * 0.20
    qty = int(max_position_value / price)

    return max(1, min(qty, qty_by_capital))
