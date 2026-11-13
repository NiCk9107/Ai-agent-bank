"""
Скринер: поиск кандидатов по правилам.
Правило Этапа 2: RSI(14) < 30 и цена выше SMA200
(перепроданность внутри восходящего долгосрочного тренда).
"""
from __future__ import annotations

import pandas as pd

from config import WATCHLIST
from analytics.indicators import compute_indicators
from db.database import get_candles_df


def screen_oversold_in_uptrend(
    rsi_below: float = 30.0,
    min_history: int = 210,
    tickers: list[str] | None = None,
) -> list[dict]:
    tickers = tickers or WATCHLIST
    results = []

    for ticker in tickers:
        df = get_candles_df(ticker, "1D")
        if len(df) < min_history:
            continue

        last = compute_indicators(df).iloc[-1]

        if pd.isna(last["rsi14"]) or pd.isna(last["sma200"]):
            continue

        if last["rsi14"] < rsi_below and last["close"] > last["sma200"]:
            results.append({
                "ticker": ticker,
                "date": last["ts"].date(),
                "close": round(float(last["close"]), 2),
                "rsi14": round(float(last["rsi14"]), 1),
                "sma200": round(float(last["sma200"]), 2),
            })

    return sorted(results, key=lambda x: x["rsi14"])