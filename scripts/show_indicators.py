"""
Сверка на глаз: python scripts/show_indicators.py SBER --rows 10
"""
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analytics.indicators import compute_indicators
from db.database import get_candles_df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker")
    parser.add_argument("--rows", type=int, default=10)
    args = parser.parse_args()

    df = get_candles_df(args.ticker.upper(), "1D")
    if df.empty:
        print("Нет данных в БД по этому тикеру")
        return

    ind = compute_indicators(df).tail(args.rows)
    cols = ["ts", "close", "rsi14", "sma50", "sma200", "macd", "atr14"]
    print(ind[cols].to_string(index=False, float_format=lambda x: f"{x:.2f}"))


if __name__ == "__main__":
    main()