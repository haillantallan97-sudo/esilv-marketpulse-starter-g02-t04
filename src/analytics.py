
import pandas as pd


def _validate_prices(prices: pd.Series) -> pd.Series:
    
    clean = prices.dropna().sort_index()
    if clean.empty:
        raise ValueError("Price series is empty.")
    if clean.index.has_duplicates:
        raise ValueError("Price series contains duplicate dates.")
    if (clean <= 0).any():
        raise ValueError("Prices must be strictly positive.")
    return clean


def align_series(
    instrument: pd.Series, benchmark: pd.Series
) -> tuple[pd.Series, pd.Series]:
    
    instrument = _validate_prices(instrument)
    benchmark = _validate_prices(benchmark)
    common = instrument.index.intersection(benchmark.index).sort_values()
    if common.empty:
        raise ValueError("Instrument and benchmark have no common date.")
    return instrument.loc[common], benchmark.loc[common]


def calculate_period_return(prices: pd.Series) -> float:
    
    clean = _validate_prices(prices)
    return float(clean.iloc[-1] / clean.iloc[0] - 1)


def normalize_base_100(prices: pd.Series) -> pd.Series:
    
    clean = _validate_prices(prices)
    return clean / clean.iloc[0] * 100


def calculate_relative_performance(
    instrument: pd.Series, benchmark: pd.Series
) -> float:
    
    instrument, benchmark = align_series(instrument, benchmark)
    return calculate_period_return(instrument) - calculate_period_return(benchmark)