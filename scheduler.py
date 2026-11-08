from datetime import timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import WATCHLIST, TIMEZONE, now_moscow
from db.database import (
    init_db,
    get_last_ts,
    save_candles,
    save_macro,
    save_trading_calendar,
    is_trading_day,
    log_event,
)
from collectors.moex_iss import fetch_candles, fetch_trading_calendar
from collectors.cbr import get_key_rate, get_usd_rate
from validation import validate_candles


def update_candles(timeframe: str) -> None:
    """
    Обновление свечей по всем тикерам из WATCHLIST.
    """
    interval = {
        "1D": 24,
        "1H": 60,
    }[timeframe]

    today = now_moscow().date()

    if not is_trading_day(today):
        log_event(
            "scheduler",
            {
                "message": f"Пропуск обновления {timeframe}: сегодня не торговый день",
                "date": str(today),
            },
        )
        return

    for ticker in WATCHLIST:
        try:
            last_ts = get_last_ts(ticker, timeframe)

            if last_ts is None:
                from_date = today - timedelta(days=30)
            else:
                from_date = last_ts.date()

            df = fetch_candles(
                ticker=ticker,
                interval=interval,
                from_date=from_date,
                till_date=today,
            )

            if df.empty:
                continue

            valid_df, issues = validate_candles(
                df=df,
                timeframe=timeframe,
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

            if saved:
                log_event(
                    "data_update",
                    {
                        "ticker": ticker,
                        "timeframe": timeframe,
                        "saved_rows": saved,
                    },
                )

        except Exception as e:
            log_event(
                "error",
                {
                    "source": "update_candles",
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "error": str(e),
                },
            )


def job_update_candles() -> None:
    """
    Ежедневное обновление дневных и часовых свечей.
    """
    update_candles("1D")
    update_candles("1H")


def job_update_macro() -> None:
    """
    Обновление макро-данных: ставка ЦБ и курс рубля.
    """
    try:
        key_rate = get_key_rate()
        usd_rate = get_usd_rate()

        save_macro(
            key_rate=key_rate,
            usdrub=usd_rate,
            brent=None,
        )

        log_event(
            "macro_update",
            {
                "key_rate": key_rate,
                "usdrub": usd_rate,
            },
        )

    except Exception as e:
        log_event(
            "error",
            {
                "source": "update_macro",
                "error": str(e),
            },
        )


def job_update_calendar() -> None:
    """
    Еженедельное обновление торгового календаря.
    """
    try:
        today = now_moscow().date()

        from_date = today - timedelta(days=365)
        till_date = today + timedelta(days=365)

        df = fetch_trading_calendar(from_date, till_date)
        saved = save_trading_calendar(df)

        log_event(
            "calendar_update",
            {
                "saved_rows": saved,
            },
        )

    except Exception as e:
        log_event(
            "error",
            {
                "source": "update_calendar",
                "error": str(e),
            },
        )


if __name__ == "__main__":
    init_db()

    scheduler = BlockingScheduler(timezone=TIMEZONE)

    # Раз в неделю обновляем торговый календарь
    scheduler.add_job(
        job_update_calendar,
        CronTrigger(
            day_of_week="sun",
            hour=2,
            minute=0,
            timezone=TIMEZONE,
        ),
        id="update_calendar",
    )

    # Утром обновляем макро
    scheduler.add_job(
        job_update_macro,
        CronTrigger(
            hour=9,
            minute=0,
            timezone=TIMEZONE,
        ),
        id="update_macro_morning",
    )

    # Вечером обновляем макро
    scheduler.add_job(
        job_update_macro,
        CronTrigger(
            hour=19,
            minute=0,
            timezone=TIMEZONE,
        ),
        id="update_macro_evening",
    )

    # После закрытия основной сессии обновляем свечи
    scheduler.add_job(
        job_update_candles,
        CronTrigger(
            day_of_week="mon-fri",
            hour=19,
            minute=5,
            timezone=TIMEZONE,
        ),
        id="update_candles",
    )

    print("Планировщик запущен.")
    print("Нажмите Ctrl+C для остановки.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Планировщик остановлен.")