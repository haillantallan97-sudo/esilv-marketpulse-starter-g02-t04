"""Fournisseur Bloomberg pour MarketPulse.

Convertit les séries Bloomberg au format canonique MarketPulse, identique à
celui du fournisseur Yahoo : date, ticker, open, high, low, close, volume.

Modes :
- APPROVED_SAMPLE (par défaut) : lecture du JSON approuvé
  data/sample/bloomberg_reference_sample.json, sans Terminal Bloomberg ;
- LIVE : point d'extension non implémenté (lève NotImplementedError).

Voir docs/BLOOMBERG_FIELD_MAPPING.md.
"""

import json
from pathlib import Path

SAMPLE_FILENAME = "bloomberg_reference_sample.json"

# Emplacements possibles du JSON approuvé, selon le dossier d'exécution
# (racine du dépôt, notebooks/, ou import depuis n'importe où).
CANDIDATE_PATHS = [
    Path(__file__).resolve().parents[2] / "data" / "sample" / SAMPLE_FILENAME,
    Path.cwd() / "data" / "sample" / SAMPLE_FILENAME,
    Path.cwd().parent / "data" / "sample" / SAMPLE_FILENAME,
]

# Ticker MarketPulse -> identifiant Bloomberg
BLOOMBERG_IDENTIFIERS = {
    "AAPL": "AAPL US Equity",
    "SP500": "SPX Index",
}

SUPPORTED_MODES = ("APPROVED_SAMPLE", "LIVE")

REQUIRED_OBSERVATION_FIELDS = {
    "observation_date",
    "open_value",
    "high_value",
    "low_value",
    "close_value",
    "volume_value",
}


def get_reference_sample_path():
    """Renvoie le chemin du JSON approuvé, quel que soit le dossier courant."""
    for path in CANDIDATE_PATHS:
        if path.exists():
            return path
    searched = ", ".join(str(path) for path in CANDIDATE_PATHS)
    raise FileNotFoundError(
        f"Approved Bloomberg sample not found. Searched: {searched}"
    )


def load_bloomberg_reference_sample(path=None):
    """Lit le payload JSON approuvé."""
    sample_path = Path(path) if path is not None else get_reference_sample_path()
    with open(sample_path, encoding="utf-8") as file:
        return json.load(file)


def find_reference_series(payload, provider_identifier):
    """Sélectionne la série correspondant à l'identifiant Bloomberg."""
    for series in payload.get("series", []):
        if series.get("provider_identifier") == provider_identifier:
            return series
    raise ValueError(
        f"Approved Bloomberg series not found: {provider_identifier}"
    )


def validate_reference_series(series):
    """Vérifie une série avant normalisation ; lève ValueError si invalide."""
    if not isinstance(series, dict):
        raise ValueError("Bloomberg series must be a dictionary.")

    ticker = series.get("canonical_ticker")
    if not ticker:
        raise ValueError("Bloomberg series has no canonical_ticker.")

    observations = series.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError(
            f"Bloomberg series {ticker} has no observations (missing or empty list)."
        )

    seen_dates = set()
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            raise ValueError(
                f"Observation #{index} of {ticker} must be a dictionary."
            )
        missing = REQUIRED_OBSERVATION_FIELDS - set(observation)
        if missing:
            raise ValueError(
                f"Observation #{index} of {ticker} is missing field(s): "
                f"{', '.join(sorted(missing))}."
            )
        date = observation["observation_date"]
        if date in seen_dates:
            raise ValueError(
                f"Duplicate observation_date {date} in series {ticker}."
            )
        seen_dates.add(date)


def normalize_reference_series(series):
    """Convertit une série Bloomberg en liste d'observations canoniques."""
    validate_reference_series(series)
    ticker = series["canonical_ticker"]
    rows = []
    for obs in series["observations"]:
        rows.append({
            "date": obs["observation_date"],
            "ticker": ticker,
            "open": float(obs["open_value"]),
            "high": float(obs["high_value"]),
            "low": float(obs["low_value"]),
            "close": float(obs["close_value"]),
            "volume": int(obs["volume_value"]),
        })
    return rows


def fetch_approved_sample_prices(provider_identifier, path=None):
    """Mode APPROVED_SAMPLE : lit le JSON approuvé et normalise la série."""
    payload = load_bloomberg_reference_sample(path)
    series = find_reference_series(payload, provider_identifier)
    return normalize_reference_series(series)


def fetch_raw_bloomberg_history(provider_identifier):
    """Hook LIVE : accès à un Terminal Bloomberg autorisé (non implémenté)."""
    raise NotImplementedError(
        f"Bloomberg LIVE access is not configured (requested {provider_identifier})."
    )


def fetch_bloomberg_prices(ticker, mode="APPROVED_SAMPLE"):
    """Point d'entrée : renvoie les observations canoniques d'un ticker
    MarketPulse ("AAPL" ou "SP500") selon le mode demandé."""
    if ticker not in BLOOMBERG_IDENTIFIERS:
        known = ", ".join(sorted(BLOOMBERG_IDENTIFIERS))
        raise ValueError(
            f"Unknown MarketPulse ticker for Bloomberg: {ticker!r}. "
            f"Known tickers: {known}."
        )
    provider_id = BLOOMBERG_IDENTIFIERS[ticker]

    if mode == "APPROVED_SAMPLE":
        return fetch_approved_sample_prices(provider_id)
    if mode == "LIVE":
        _raw = fetch_raw_bloomberg_history(provider_id)
        raise NotImplementedError("Live mode not currently active.")
    raise ValueError(
        f"Unrecognized Bloomberg mode: {mode!r}. Supported: {', '.join(SUPPORTED_MODES)}."
    )
