import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.append(str(Path(__file__).resolve().parents[1]))

from collectors.moex_iss import fetch_trading_calendar
from db.database import init_db, save_trading_calendar, log_event


def main():
    init_db()

    today = date.today()
    from_date = today - timedelta(days=365 * 10 + 60)
    till_date = today + timedelta(days=365)

    df = fetch_trading_calendar(from_date, till_date)
    print("Получено строк календаря:", len(df))

    if not df.empty:
        print(df.head(3))
        print(df.tail(3))

    saved = save_trading_calendar(df)
    log_event("calendar_reload", {"rows": saved})
    print("Сохранено:", saved)


if __name__ == "__main__":
    main()