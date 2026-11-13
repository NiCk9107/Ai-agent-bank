"""
График: python scripts/make_chart.py SBER --days 365 --levels 291,331
"""
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analytics.indicators import compute_indicators
from charts.candles import render_candle_chart
from db.database import get_candles_df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker")
    parser.add_argument("--timeframe", default="1D")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--levels", default=None, help="через запятую: 291,331")
    args = parser.parse_args()

    levels = [float(x) for x in args.levels.split(",")] if args.levels else None

    df = get_candles_df(args.ticker.upper(), args.timeframe)
    if df.empty:
        print("Нет данных в БД по этому тикеру")
        return

    ind = compute_indicators(df)
    path = render_candle_chart(
        ind, args.ticker.upper(), args.timeframe, days=args.days, levels=levels
    )
    print("График сохранён:", path)

    last = ind.iloc[-1]
    print(
        f"Последний бар {last['ts'].date()}: close={last['close']:.2f} "
        f"RSI14={last['rsi14']:.1f} SMA50={last['sma50']:.2f} "
        f"SMA200={last['sma200']:.2f} ATR14={last['atr14']:.2f}"
    )


if __name__ == "__main__":
    main()