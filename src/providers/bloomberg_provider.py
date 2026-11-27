import json
from pathlib import Path

SAMPLE_FILE = Path("data") / "sample" / "bloomberg_reference_sample.json"

# Le module peut etre lance depuis la racine du depot ou depuis notebooks/
CANDIDATE_PATHS = [
    Path(__file__).resolve().parents[2] / SAMPLE_FILE,
    Path.cwd() / SAMPLE_FILE,
    Path.cwd().parent / SAMPLE_FILE,
]

BLOOMBERG_IDENTIFIERS = {
    "AAPL": "AAPL US Equity",
    "SP500": "SPX Index",
}

REQUIRED_FIELDS = {
    "observation_date",
    "open_value",
    "high_value",
    "low_value",
    "close_value",
    "volume_value",
}


def get_reference_sample_path():
    for path in CANDIDATE_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Approved Bloomberg sample not found: {SAMPLE_FILE}"
    )


def load_bloomberg_reference_sample():
    with open(get_reference_sample_path(), encoding="utf-8") as file:
        return json.load(file)


def find_reference_series(payload, provider_identifier):
    for series in payload.get("series", []):
        if series.get("provider_identifier") == provider_identifier:
            return series

    raise ValueError(
        f"Approved Bloomberg series not found: {provider_identifier}"
    )


def validate_reference_series(series):
    ticker = series.get("canonical_ticker")
    if not ticker:
        raise ValueError("Bloomberg series without canonical_ticker.")

    observations = series.get("observations")
    if not isinstance(observations, list) or len(observations) == 0:
        raise ValueError(f"No observations for {ticker}.")

    seen_dates = set()
    for position, obs in enumerate(observations, start=1):
        missing = REQUIRED_FIELDS - set(obs)
        if missing:
            raise ValueError(
                f"{ticker}, observation {position}: missing fields "
                f"{sorted(missing)}."
            )

        date = obs["observation_date"]
        if date in seen_dates:
            raise ValueError(f"{ticker}: duplicate observation date {date}.")
        seen_dates.add(date)


def normalize_reference_series(series):
    validate_reference_series(series)

    rows = []
    for obs in series["observations"]:
        rows.append({
            "date": obs["observation_date"],
            "ticker": series["canonical_ticker"],
            "open": float(obs["open_value"]),
            "high": float(obs["high_value"]),
            "low": float(obs["low_value"]),
            "close": float(obs["close_value"]),
            "volume": int(obs["volume_value"]),
        })
    return rows


def fetch_approved_sample_prices(provider_identifier):
    payload = load_bloomberg_reference_sample()
    series = find_reference_series(payload, provider_identifier)
    return normalize_reference_series(series)


def fetch_raw_bloomberg_history(provider_identifier):
    # Hook LIVE : necessite un Terminal Bloomberg autorise, non disponible ici.
    raise NotImplementedError(
        f"Bloomberg LIVE access not configured for {provider_identifier}."
    )


def fetch_bloomberg_prices(ticker, mode="APPROVED_SAMPLE"):
    if ticker not in BLOOMBERG_IDENTIFIERS:
        raise ValueError(f"Unknown MarketPulse ticker: {ticker}")

    provider_id = BLOOMBERG_IDENTIFIERS[ticker]

    if mode == "APPROVED_SAMPLE":
        return fetch_approved_sample_prices(provider_id)
    elif mode == "LIVE":
        _raw = fetch_raw_bloomberg_history(provider_id)
        raise NotImplementedError("Live mode not currently active.")
    else:
        raise ValueError(f"Unrecognized Bloomberg mode: {mode}")
