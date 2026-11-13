"""
Этап 2: технические индикаторы.

Все формулы считает код (никакой LLM).
RSI и ATR — со сглаживанием Уайлдера, как в классических
терминалах (TradingView, терминал брокера).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Простая скользящая средняя."""
    return series.rolling(window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    """Экспоненциальная скользящая средняя."""
    return series.ewm(span=span, adjust=False).mean()


def _wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """
    Сглаживание Уайлдера (RMA).

    Затравка: простое среднее первых `period` значений,
    затем рекурсия: out[i] = (out[i-1] * (period - 1) + x[i]) / period
    """
    x = series.to_numpy(dtype=float)
    n = len(x)
    out = np.full(n, np.nan)

    if n <= period:
        return pd.Series(out, index=series.index)

    out[period] = np.mean(x[1:period + 1])
    for i in range(period + 1, n):
        out[i] = (out[i - 1] * (period - 1) + x[i]) / period

    return pd.Series(out, index=series.index)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI (индекс относительной силы) со сглаживанием Уайлдера."""
    delta = close.diff()
    gain = delta.clip(lower=0.0).fillna(0.0)
    loss = (-delta).clip(lower=0.0).fillna(0.0)

    avg_gain = _wilder_smooth(gain, period)
    avg_loss = _wilder_smooth(loss, period)

    with np.errstate(divide="ignore", invalid="ignore"):
        rs = avg_gain / avg_loss

    result = 100.0 - 100.0 / (1.0 + rs)

    # Если средний убыток = 0 (в т.ч. плоский рынок) — RSI = 100.
    # Но только там, где сглаживание уже посчитано: зону прогрева (NaN) не трогаем.
    result = result.mask((avg_loss == 0) & avg_loss.notna(), 100.0)
    return result


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD. Возвращает (линия MACD, сигнальная линия, гистограмма)."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def true_range(df: pd.DataFrame) -> pd.Series:
    """Истинный размах (True Range)."""
    prev_close = df["close"].shift(1)
    return pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR (средний истинный размах) со сглаживанием Уайлдера."""
    return _wilder_smooth(true_range(df), period)


def avg_volume(volume: pd.Series, window: int = 20) -> pd.Series:
    """Средний объём за window дней."""
    return volume.rolling(window).mean()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Принимает DataFrame с колонками open/high/low/close/volume/ts,
    возвращает копию с добавленными колонками индикаторов.

    Важно: считайте индикаторы по ВСЕЙ истории, а потом отрезайте
    хвост для графика — иначе SMA200 на краю будет неверным.
    """
    out = df.copy()
    macd_line, signal_line, hist = macd(out["close"])

    out["sma50"] = sma(out["close"], 50)
    out["sma200"] = sma(out["close"], 200)
    out["rsi14"] = rsi(out["close"], 14)
    out["macd"] = macd_line
    out["macd_signal"] = signal_line
    out["macd_hist"] = hist
    out["atr14"] = atr(out, 14)
    out["volume_avg20"] = avg_volume(out["volume"], 20)
    return out