def moving_average_signal(prices):
    """
    Simple 3-vs-5 moving-average strategy.

    BUY  -> short MA > long MA
    SELL -> short MA < long MA
    HOLD -> insufficient data / equal
    """

    if len(prices) < 5:
        return "HOLD"

    short_ma = sum(prices[-3:]) / 3
    long_ma = sum(prices[-5:]) / 5

    if short_ma > long_ma:
        return "BUY"

    if short_ma < long_ma:
        return "SELL"

    return "HOLD"
