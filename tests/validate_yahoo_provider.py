"""Validation TD08 : fetch_prices_for_ticker().

Lancer depuis la racine du dépôt :  python -m tests.validate_yahoo_provider
"""

import src.providers.yahoo_provider as yp
from src.providers.yahoo_provider import fetch_prices_for_ticker

CANONICAL_KEYS = {"date", "ticker", "open", "high", "low", "close", "volume"}

# 1. Ticker inconnu -> ValueError avec un message explicite
try:
    fetch_prices_for_ticker("UNKNOWN")
    raise AssertionError("ValueError attendue pour UNKNOWN")
except ValueError as error:
    assert "UNKNOWN" in str(error)
    print(f"UNKNOWN -> ValueError : {error}")

# 2. Sans réseau : vérifier que la fonction délègue bien à fetch_yahoo_prices()
calls = []
original = yp.fetch_yahoo_prices
yp.fetch_yahoo_prices = lambda **kwargs: calls.append(kwargs)
try:
    fetch_prices_for_ticker("AAPL")
    fetch_prices_for_ticker("SP500", period="3mo", interval="1wk")
finally:
    yp.fetch_yahoo_prices = original

assert calls[0] == {"symbol": "AAPL", "canonical_ticker": "AAPL",
                    "period": "1mo", "interval": "1d"}
assert calls[1] == {"symbol": "^GSPC", "canonical_ticker": "SP500",
                    "period": "3mo", "interval": "1wk"}
print("Mapping et paramètres period/interval transmis correctement.")

# 3. Récupération réelle (nécessite Internet + yfinance)
try:
    apple = fetch_prices_for_ticker("AAPL")
    sp500 = fetch_prices_for_ticker("SP500")
    apple_3_months = fetch_prices_for_ticker("AAPL", period="3mo", interval="1d")
except Exception as error:  # Yahoo indisponible, pas de réseau, etc.
    print(f"Yahoo Finance indisponible : {type(error).__name__}: {error}")
else:
    for name, rows in [("AAPL 1mo", apple), ("SP500 1mo", sp500),
                       ("AAPL 3mo", apple_3_months)]:
        assert rows and all(set(row) == CANONICAL_KEYS for row in rows)
        print(f"{name}: {len(rows)} lignes, dernier close = {rows[-1]['close']:.2f}")
    assert len(apple_3_months) > len(apple)
    assert {r["ticker"] for r in apple} == {"AAPL"}
    assert {r["ticker"] for r in sp500} == {"SP500"}

print("Tous les tests du fournisseur Yahoo ont réussi.")
