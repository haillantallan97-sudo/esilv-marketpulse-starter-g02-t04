from pathlib import Path
import csv
import json


DATA_DIR = Path("data/sample")

# These starter values mirror config/settings.yml.
# settings.yml is a human-readable configuration contract in the CORE.
# Parsing YAML is optional and is not required by the 18-hour lab sequence.
LOOKBACK_LABEL = "1 month"
INTERVAL_LABEL = "Daily"


def load_instruments():
    with open(DATA_DIR / "instruments.json", encoding="utf-8") as file:
        return json.load(file)


def load_prices():
    with open(DATA_DIR / "prices.csv", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def filter_prices(prices, ticker):
    return [row for row in prices if row["ticker"] == ticker]

def display_market_summary(asset, prices,
        show_currency=True):
    print(f"\n{asset['ticker']} - {asset['name']}")
    print(f"Observations : {len(prices)}")
    print(f"first date : {get_first_date(prices)}")
    print(f"last date : {get_last_date(prices)}")
    
    first_close = float(prices[0]["close"])
    last_close = float(prices[-1]["close"])
    
    if show_currency:
        print(f"First close : {first_close:.2f} {asset['currency']}")
        print(f"Last close  : {last_close:.2f} {asset['currency']}")
    else:
        print(f"First close : {first_close:.2f}")
        print(f"Last close  : {last_close:.2f}")

def get_first_date(prices):
    return prices[0]["date"]


def get_last_date(prices):
    return prices[-1]["date"]


def main():
    instruments = load_instruments()
    prices = load_prices()

    instrument = instruments["instrument"]
    benchmark = instruments["benchmark"]

    instrument_prices = filter_prices(prices, instrument["ticker"])
    benchmark_prices = filter_prices(prices, benchmark["ticker"])

    instrument_latest = instrument_prices[-1]
    benchmark_latest = benchmark_prices[-1]

    print("=== MarketPulse ===")
    print()
    print("Instrument")
    print(f"{instrument['ticker']} - {instrument['name']}")
    print(f"Last price: {instrument_latest['close']} {instrument['currency']}")
    print()
    print("Benchmark")
    print(f"{benchmark['ticker']} - {benchmark['name']}")
    print(f"Last level: {benchmark_latest['close']}")
    print()
    print(f"Period: {LOOKBACK_LABEL}")
    print(f"Interval: {INTERVAL_LABEL}")
    print()
    print("Observations")
    print(f"{instrument['ticker']}: {len(instrument_prices)}")
    print(f"{benchmark['ticker']}: {len(benchmark_prices)}")

    print("\nInstrument")
    display_market_summary(instrument, instrument_prices, show_currency=True)
    
    print("\nBenchmark")
    display_market_summary(benchmark, benchmark_prices, show_currency=False)


if _name_ == "_main_":
    main()

    