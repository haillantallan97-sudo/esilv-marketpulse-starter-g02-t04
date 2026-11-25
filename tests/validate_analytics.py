import math

import pandas as pd

from src.analytics import (align_series, calculate_period_return,
                           calculate_relative_performance, normalize_base_100)

dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])
instrument = pd.Series([100, 110, 121], index=dates)
benchmark = pd.Series([200, 210, 220], index=dates)

assert math.isclose(calculate_period_return(instrument), 0.21)
assert math.isclose(calculate_period_return(benchmark), 0.10)
assert normalize_base_100(benchmark).round(9).tolist() == [100, 105, 110]
assert math.isclose(calculate_relative_performance(instrument, benchmark), 0.11)

shifted = benchmark.set_axis(dates + pd.Timedelta(days=1))
a, b = align_series(instrument, shifted)
assert len(a) == 2 and a.index.equals(b.index)

try:
    calculate_period_return(pd.Series(dtype=float))
    raise AssertionError("ValueError expected")
except ValueError:
    pass

print("OK")