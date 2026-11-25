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

def get_first_close(prices):
    return float(prices[0]["close"])


def get_last_close(prices):
    return float(prices[-1]["close"])

def get_first_date(prices):
    return prices[0]["date"]


def get_last_date(prices):
    return prices[-1]["date"]

def display_market_summary(asset, prices, show_currency=True):
    print("--- Market summary ---")
    print(asset["ticker"], "-", asset["name"])
    print("Market :", asset["market"])
    print("Observations :", len(prices))
    print("First date :", get_first_date(prices))
    print("Last date  :", get_last_date(prices))

    first_close = get_first_close(prices)
    last_close = get_last_close(prices)

    if show_currency:
        currency = " " + asset["currency"]
    else:
        currency = ""

    print("First close :", f"{first_close:.2f}" + currency)
    print("Last close  :", f"{last_close:.2f}" + currency)
    print()


def main():
    instruments = load_instruments()
    prices = load_prices()

    instrument = instruments["instrument"]
    benchmark = instruments["benchmark"]

    instrument_prices = filter_prices(
        prices, instrument["ticker"]
    )
    benchmark_prices = filter_prices(
        prices, benchmark["ticker"]
    )

    print("=== MarketPulse ===")
    print()
    print("Market configuration")
    print("Period   : 1 month")
    print("Interval : Daily")
    print()

    print("Instrument")
    display_market_summary(instrument, instrument_prices)

    print("Benchmark")
    display_market_summary(
        benchmark, benchmark_prices, show_currency=False
    )


if __name__ == "__main__":
    main()
