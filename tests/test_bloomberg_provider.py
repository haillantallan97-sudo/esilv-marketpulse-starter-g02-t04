"""Tests TD10 du fournisseur Bloomberg (mode APPROVED_SAMPLE uniquement).

A lancer depuis la racine du depot :
    python -m tests.test_bloomberg_provider
"""

import json

from src.providers.bloomberg_provider import (
    fetch_bloomberg_prices,
    get_reference_sample_path,
    normalize_reference_series,
)

CANONICAL_KEYS = {"date", "ticker", "open", "high", "low", "close", "volume"}


def make_obs(date="2026-11-18"):
    # Donnees fictives : elles testent la conversion, pas une extraction Bloomberg
    return {
        "observation_date": date,
        "open_value": "100.0",
        "high_value": "112.0",
        "low_value": "99.0",
        "close_value": "110.0",
        "volume_value": "1500",
    }


def assert_value_error(series, name):
    try:
        normalize_reference_series(series)
    except ValueError as exc:
        print(f"[OK] {name} -> ValueError : {exc}")
    else:
        raise AssertionError(f"{name} : ValueError attendue")


def test_complete_observation():
    rows = normalize_reference_series(
        {"canonical_ticker": "AAPL", "observations": [make_obs()]}
    )
    assert len(rows) == 1
    assert set(rows[0]) == CANONICAL_KEYS
    assert rows[0]["ticker"] == "AAPL"
    assert rows[0]["date"] == "2026-11-18"
    assert rows[0]["close"] == 110.0
    assert isinstance(rows[0]["close"], float)
    assert isinstance(rows[0]["volume"], int)
    print("[OK] observation complete -> liste canonique valide")


def test_invalid_series():
    assert_value_error(
        {"canonical_ticker": "AAPL", "observations": []},
        "liste observations vide",
    )

    obs = make_obs()
    del obs["close_value"]
    assert_value_error(
        {"canonical_ticker": "AAPL", "observations": [obs]},
        "close_value absent",
    )

    assert_value_error(
        {"canonical_ticker": "AAPL",
         "observations": [make_obs(), make_obs()]},
        "dates dupliquees",
    )

    assert_value_error(
        {"canonical_ticker": "AAPL",
         "observations": [{"observation_date": "2026-11-18"}]},
        "champs manquants",
    )


def test_modes_and_tickers():
    for kwargs, error in [
        ({"ticker": "MSFT"}, ValueError),
        ({"ticker": "AAPL", "mode": "TEST"}, ValueError),
        ({"ticker": "AAPL", "mode": "LIVE"}, NotImplementedError),
    ]:
        try:
            fetch_bloomberg_prices(**kwargs)
        except error:
            print(f"[OK] {kwargs} -> {error.__name__}")
        else:
            raise AssertionError(f"{kwargs} : {error.__name__} attendue")


def test_approved_sample_matches_expected():
    aapl = fetch_bloomberg_prices("AAPL", mode="APPROVED_SAMPLE")
    sp500 = fetch_bloomberg_prices("SP500", mode="APPROVED_SAMPLE")
    assert len(aapl) > 0 and len(sp500) > 0
    assert all(row["ticker"] == "AAPL" for row in aapl)
    assert all(row["ticker"] == "SP500" for row in sp500)
    print("Bloomberg stage - APPROVED_SAMPLE")
    print("AAPL:", len(aapl), "SP500:", len(sp500))

    # Comparaison valeur par valeur, pas seulement la presence du fichier
    expected_path = get_reference_sample_path().with_name(
        "bloomberg_reference_expected.json"
    )
    with open(expected_path, encoding="utf-8") as file:
        expected = json.load(file)["rows"]

    actual = aapl + sp500
    assert len(actual) == len(expected), (len(actual), len(expected))
    for i, (got, want) in enumerate(zip(actual, expected)):
        assert got == want, f"ligne {i} : {got} != {want}"
    print(f"[OK] {len(expected)} lignes identiques au fichier expected")


if __name__ == "__main__":
    test_complete_observation()
    test_invalid_series()
    test_modes_and_tickers()
    test_approved_sample_matches_expected()
    print("Tous les tests Bloomberg passent (APPROVED_SAMPLE).")
