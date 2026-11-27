import yfinance as yf

YAHOO_SYMBOL_MAPPING = {
    "AAPL": "AAPL",
    "SP500": "^GSPC"
}


def fetch_yahoo_prices(symbol, canonical_ticker, period="1mo", interval="1d"):
    history = yf.Ticker(symbol).history(
        period=period,
        interval=interval,
        auto_adjust=False
    )

    if history.empty:
        raise ValueError(
            f"No Yahoo Finance data returned for symbol {symbol}."
        )

    rows = []

    for timestamp, row in history.iterrows():
        rows.append({
            "date": timestamp.strftime("%Y-%m-%d"),
            "ticker": canonical_ticker,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"])
        })

    return rows


def fetch_prices_for_ticker(ticker, period="1mo", interval="1d"):
    """Récupère les prix d'un identifiant MarketPulse (ex. "AAPL", "SP500")
    en retrouvant automatiquement son symbole Yahoo."""
    if ticker not in YAHOO_SYMBOL_MAPPING:
        known = ", ".join(sorted(YAHOO_SYMBOL_MAPPING))
        raise ValueError(
            f"Unknown MarketPulse ticker: {ticker!r}. Known tickers: {known}."
        )
    return fetch_yahoo_prices(
        symbol=YAHOO_SYMBOL_MAPPING[ticker],
        canonical_ticker=ticker,
        period=period,
        interval=interval,
    )
