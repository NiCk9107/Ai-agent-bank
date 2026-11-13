"""PNG-графики свечей для бота и визуальной проверки."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # без окон: работает и на сервере

import mplfinance as mpf
import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def render_candle_chart(
    df: pd.DataFrame,
    ticker: str,
    timeframe: str = "1D",
    days: int = 365,
    levels: list[float] | None = None,
    out_dir: Path | str | None = None,
) -> Path:
    """
    Строит свечной график с SMA50/200 и объёмами.

    df — DataFrame с колонками ts, open, high, low, close, volume
         и (желательно) sma50, sma200, посчитанными по ВСЕЙ истории.
    levels — горизонтальные линии (например, стоп и цель).
    Возвращает путь к PNG.
    """
    out_dir = Path(out_dir) if out_dir else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    d = df.tail(days).copy()
    d.index = pd.DatetimeIndex(d["ts"])
    d = d.rename(columns=str.title)

    plot_df = d[["Open", "High", "Low", "Close", "Volume"]].astype(float)

    addplots = []
    if "Sma50" in d.columns and d["Sma50"].notna().any():
        addplots.append(mpf.make_addplot(d["Sma50"], color="orange", width=1.0))
    if "Sma200" in d.columns and d["Sma200"].notna().any():
        addplots.append(mpf.make_addplot(d["Sma200"], color="blue", width=1.0))

    kwargs = dict(
        type="candle",
        volume=True,
        style="charles",
        title=f"\n{ticker} · {timeframe} · последних баров: {len(plot_df)}",
        figsize=(12, 7),
        warn_too_much_data=5000,
    )
    if addplots:
        kwargs["addplot"] = addplots
    if levels:
        kwargs["hlines"] = dict(
            hlines=levels, colors=["red"], linewidths=1, linestyle="--"
        )

    path = out_dir / f"{ticker}_{timeframe}_{days}d.png"
    kwargs["savefig"] = dict(fname=path, dpi=150, bbox_inches="tight")
    mpf.plot(plot_df, **kwargs)
    return path