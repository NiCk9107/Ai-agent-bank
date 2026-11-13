import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analytics.indicators import sma, rsi, macd, atr, compute_indicators


def wilder_rsi_reference(prices, period=14):
    """Эталонный RSI «вручную»: классический алгоритм Уайлдера циклом."""
    gains, losses = [], []
    for i in range(1, len(prices)):
        d = prices[i] - prices[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    def to_rsi(ag, al):
        if al == 0:
            return 100.0
        return 100.0 - 100.0 / (1.0 + ag / al)

    out = [to_rsi(avg_gain, avg_loss)]
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out.append(to_rsi(avg_gain, avg_loss))
    return out


def test_rsi_matches_manual_calculation():
    prices = [
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
        45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00,
        46.03, 46.41, 46.22, 45.64, 46.21, 46.25, 45.71, 46.45,
        45.78, 45.35, 44.03, 44.18, 44.22, 44.57, 43.58, 42.66,
        43.13,
    ]
    got = rsi(pd.Series(prices, dtype=float), 14).dropna().to_numpy()
    expected = wilder_rsi_reference(prices, 14)
    assert len(got) == len(expected)
    assert np.allclose(got, expected, atol=1e-9)


def test_sma_known_values():
    out = sma(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]), 3)
    assert np.isnan(out.iloc[1])
    assert out.iloc[2] == pytest.approx(2.0)
    assert out.iloc[3] == pytest.approx(3.0)
    assert out.iloc[4] == pytest.approx(4.0)


def test_rsi_bounds():
    rng = np.random.default_rng(7)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 500)))
    r = rsi(close).dropna()
    assert ((r >= 0) & (r <= 100)).all()


def test_rsi_uptrend_above_50():
    close = pd.Series(np.linspace(100, 200, 120))
    assert (rsi(close).dropna() > 50).all()


def test_macd_hist_identity():
    rng = np.random.default_rng(3)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 300)))
    line, signal, hist = macd(close)
    assert np.allclose(hist.dropna(), (line - signal).dropna())


def test_atr_positive():
    rng = np.random.default_rng(11)
    n = 300
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    df = pd.DataFrame({
        "high": close + rng.uniform(0.2, 1.5, n),
        "low": close - rng.uniform(0.2, 1.5, n),
        "close": close,
    })
    assert (atr(df).dropna() > 0).all()


def test_compute_indicators_columns():
    n = 250
    rng = np.random.default_rng(5)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, n)))  # <-- Series, не ndarray
    df = pd.DataFrame({
        "ts": pd.date_range("2024-01-01", periods=n, freq="B"),
        "open": close.shift(1).fillna(close.iloc[0]),
        "high": close + 1,
        "low": close - 1,
        "close": close,
        "volume": rng.integers(1_000_000, 5_000_000, n),
    })
    out = compute_indicators(df)
    for col in ["sma50", "sma200", "rsi14", "macd", "macd_signal",
                "macd_hist", "atr14", "volume_avg20"]:
        assert col in out.columns
    assert out["rsi14"].notna().sum() == n - 14