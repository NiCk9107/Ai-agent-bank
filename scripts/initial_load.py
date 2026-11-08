import sys
import argparse
import time
from pathlib import Path
from datetime import timedelta

# Добавляем корень проекта в PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import WATCHLIST, now_moscow
from db.database import (
    init_db,
    save_securities,
    save_trading_calendar,
    save_candles,
    get_trading_dates,
    log_event,
)
from collectors.moex_iss import (
    fetch_candles,
    fetch_trading_calendar,
)
from validation import validate_candles


def parse_args():
    parser = argparse.ArgumentParser(
        description="Первичная загрузка исторических данных рынка РФ"
    )

    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Список тикеров через запятую. По умолчанию используется WATCHLIST.",
    )

    parser.add_argument(
        "--timeframes",
        type=str,
        default="1D",
        help="Таймфреймы через запятую: 1D,1H. По умолчанию 1D.",
    )

    parser.add_argument(
        "--years",
        type=int,
        default=None,
        help="Сколько лет истории грузить. Если не указано: 10 лет для 1D и 5 лет для 1H.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    tickers = (
        [x.strip().upper() for x in args.tickers.split(",") if x.strip()]
        if args.tickers
        else WATCHLIST
    )

    timeframes = [x.strip().upper() for x in args.timeframes.split(",") if x.strip()]

    print("Инициализация базы данных...")
    init_db()

    print("Сохранение информации по бумагам...")
    save_securities(tickers)

    today = now_moscow().date()

    # Грузим календарь с запасом:
    # 10 лет назад + 1 год вперёд
    calendar_from = today - timedelta(days=365 * 10 + 60)
    calendar_till = today + timedelta(days=365)

    print("Загрузка торгового календаря...")
    calendar_df = fetch_trading_calendar(calendar_from, calendar_till)
    saved_calendar = save_trading_calendar(calendar_df)
    log_event("initial_load", {"calendar_rows": saved_calendar})
    print(f"Торговый календарий сохранён: {saved_calendar} строк.")

    for timeframe in timeframes:
        if args.years:
            years = args.years
        else:
            years = 10 if timeframe == "1D" else 5

        from_date = today - timedelta(days=365 * years)
        till_date = today

        interval = 24 if timeframe == "1D" else 60

        trading_dates = None
        if timeframe == "1D":
            trading_dates = get_trading_dates(from_date, till_date)

        print(f"\nЗагрузка таймфрейма: {timeframe}, период: {from_date} - {till_date}")

        for ticker in tickers:
            print(f"{timeframe} {ticker} ...", end=" ")

            try:
                df = fetch_candles(
                    ticker=ticker,
                    interval=interval,
                    from_date=from_date,
                    till_date=till_date,
                )

                if df.empty:
                    print("нет данных")
                    continue

                valid_df, issues = validate_candles(
                    df=df,
                    timeframe=timeframe,
                    trading_dates=trading_dates,
                    from_date=from_date,
                    till_date=till_date,
                )

                for issue in issues:
                    log_event(
                        "data_validation",
                        {
                            "ticker": ticker,
                            "timeframe": timeframe,
                            "issue": issue,
                        },
                    )

                saved = save_candles(valid_df, ticker, timeframe)

                print(f"сохранено {saved}, отброшено {len(df) - len(valid_df)}")

                if issues:
                    for issue in issues:
                        print(f"  ⚠ {issue}")

            except Exception as e:
                print(f"ошибка: {e}")
                log_event(
                    "error",
                    {
                        "source": "initial_load",
                        "ticker": ticker,
                        "timeframe": timeframe,
                        "error": str(e),
                    },
                )

            time.sleep(0.5)

    print("\nПервичная загрузка завершена.")


if __name__ == "__main__":
    main()