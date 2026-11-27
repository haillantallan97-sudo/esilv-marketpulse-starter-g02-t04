"""Validation TD10 : fournisseur Bloomberg (mode APPROVED_SAMPLE).

Lancer depuis la racine du dépôt :  python -m tests.validate_bloomberg_provider
Données fictives en mémoire pour les tests unitaires ; aucun accès LIVE.
"""

import json

from src.providers.bloomberg_provider import (
    fetch_bloomberg_prices,
    get_reference_sample_path,
    normalize_reference_series,
)

CANONICAL_KEYS = {"date", "ticker", "open", "high", "low", "close", "volume"}


def fake_observation(date="2026-11-18", **overrides):
    obs = {
        "observation_date": date,
        "open_value": "100.0",
        "high_value": "112.0",
        "low_value": "99.0",
        "close_value": "110.0",
        "volume_value": "1500",
    }
    obs.update(overrides)
    return obs


def expect_value_error(series, label):
    try:
        normalize_reference_series(series)
    except ValueError as error:
        print(f"{label} : ValueError OK -> {error}")
    else:
        raise AssertionError(f"{label} : ValueError attendue")


# Cas 1 : une observation complète -> liste canonique valide
rows = normalize_reference_series(
    {"canonical_ticker": "AAPL", "observations": [fake_observation()]}
)
assert len(rows) == 1
assert set(rows[0]) == CANONICAL_KEYS
assert rows[0]["ticker"] == "AAPL"
assert rows[0]["date"] == "2026-11-18"
assert rows[0]["close"] == 110.0
assert isinstance(rows[0]["close"], float)
assert isinstance(rows[0]["volume"], int)
print("Observation complète : liste canonique valide")

# Cas 2 : liste observations vide
expect_value_error({"canonical_ticker": "AAPL", "observations": []},
                   "Observations vides")

# Cas 3 : close_value absent
obs = fake_observation()
del obs["close_value"]
expect_value_error({"canonical_ticker": "AAPL", "observations": [obs]},
                   "close_value absent")

# Cas 4 : deux dates identiques
expect_value_error(
    {"canonical_ticker": "AAPL",
     "observations": [fake_observation(), fake_observation()]},
    "Dates dupliquées",
)

# Test de robustesse de l'énoncé (sans validateur : KeyError)
expect_value_error(
    {"canonical_ticker": "AAPL",
     "observations": [{"observation_date": "2026-11-18"}]},
    "Champ manquant",
)
expect_value_error({"observations": [fake_observation()]},
                   "canonical_ticker absent")

# Ticker et mode inconnus, LIVE non simulé
for call, expected_error in [
    (lambda: fetch_bloomberg_prices("UNKNOWN"), ValueError),
    (lambda: fetch_bloomberg_prices("AAPL", mode="DEMO"), ValueError),
    (lambda: fetch_bloomberg_prices("AAPL", mode="LIVE"), NotImplementedError),
]:
    try:
        call()
    except expected_error as error:
        print(f"{expected_error.__name__} OK -> {error}")
    else:
        raise AssertionError(f"{expected_error.__name__} attendue")

# Vérification réelle sur l'échantillon approuvé
print("Référence :", get_reference_sample_path())
aapl = fetch_bloomberg_prices("AAPL", mode="APPROVED_SAMPLE")
sp500 = fetch_bloomberg_prices("SP500", mode="APPROVED_SAMPLE")
assert len(aapl) > 0 and len(sp500) > 0
assert all(row["ticker"] == "AAPL" for row in aapl)
assert all(row["ticker"] == "SP500" for row in sp500)
assert all(set(row) == CANONICAL_KEYS for row in aapl + sp500)
print("Bloomberg stage - APPROVED_SAMPLE")
print("AAPL:", len(aapl), "SP500:", len(sp500))

# Comparaison effective avec le JSON expected (pas seulement sa présence)
expected_path = get_reference_sample_path().with_name(
    "bloomberg_reference_expected.json"
)
with open(expected_path, encoding="utf-8") as file:
    expected_rows = json.load(file)["rows"]

actual_rows = aapl + sp500
assert len(actual_rows) == len(expected_rows), (
    f"{len(actual_rows)} lignes normalisées, {len(expected_rows)} attendues"
)
differences = [
    (index, actual, expected)
    for index, (actual, expected) in enumerate(zip(actual_rows, expected_rows))
    if actual != expected
]
for index, actual, expected in differences:
    print(f"Différence ligne {index} : obtenu {actual} / attendu {expected}")
assert not differences, f"{len(differences)} ligne(s) différente(s)"
print(f"Comparaison avec expected : {len(expected_rows)} lignes identiques (matching)")

print("Tous les tests du fournisseur Bloomberg ont réussi (mode APPROVED_SAMPLE).")
