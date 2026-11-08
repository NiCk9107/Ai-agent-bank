import json
import time
from datetime import datetime, date, time as dt_time
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import insert

from config import DB_PATH, now_moscow
from db.models import (
    Base,
    Security,
    Candle,
    Macro,
    Event,
    TradingDay,
)


# Создаём папку под SQLite, если её ещё нет
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, future=True)


def init_db() -> None:
    """
    Создаёт все таблицы.
    """
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()


def log_event(event_type: str, payload: dict | list | str) -> None:
    """
    Запись в журнал событий.
    """
    with SessionLocal() as session:
        session.add(
            Event(
                ts=now_moscow(),
                type=event_type,
                payload=json.dumps(payload, ensure_ascii=False, default=str),
            )
        )
        session.commit()


# ----------------------------
# Securities
# ----------------------------

def save_securities(tickers: list[str]) -> None:
    """
    Сохраняем базовую информацию по тикерам.
    Имя, лот и сектор пытаемся вытащить из ISS MOEX.
    """
    from collectors.moex_iss import fetch_security_info

    for ticker in tickers:
        try:
            info = fetch_security_info(ticker)

            stmt = insert(Security).values(
                ticker=ticker,
                name=info.get("name"),
                sector=info.get("sector"),
                lot_size=info.get("lot_size"),
                is_active=True,
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=["ticker"])

            with SessionLocal() as session:
                session.execute(stmt)
                session.commit()

            time.sleep(0.2)

        except Exception as e:
            log_event("error", {"source": "save_securities", "ticker": ticker, "error": str(e)})


# ----------------------------
# Candles
# ----------------------------

def save_candles(df, ticker: str, timeframe: str) -> int:
    """
    Сохраняем свечи в БД.
    Дубликаты игнорируются.
    """
    if df is None or df.empty:
        return 0

    records = df[["ts", "open", "high", "low", "close", "volume"]].to_dict("records")

    for row in records:
        row["ticker"] = ticker
        row["timeframe"] = timeframe

    stmt = insert(Candle).values(records)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["ticker", "timeframe", "ts"]
    )

    with SessionLocal() as session:
        session.execute(stmt)
        session.commit()

    return len(records)


def get_last_ts(ticker: str, timeframe: str):
    """
    Последняя свеча по тикеру и таймфрейму.
    """
    with SessionLocal() as session:
        return session.scalar(
            select(func.max(Candle.ts)).where(
                Candle.ticker == ticker,
                Candle.timeframe == timeframe,
            )
        )


# ----------------------------
# Trading calendar
# ----------------------------

def save_trading_calendar(df) -> int:
    """
    Сохраняем торговый календарь.
    """
    if df is None or df.empty:
        return 0

    records = df[["date", "is_trading_day"]].to_dict("records")

    stmt = insert(TradingDay).values(records)
    stmt = stmt.on_conflict_do_nothing(index_elements=["date"])

    with SessionLocal() as session:
        session.execute(stmt)
        session.commit()

    return len(records)


def get_trading_dates(from_date, till_date) -> list[date]:
    """
    Возвращает торговые дни между датами.
    """
    if isinstance(from_date, datetime):
        from_date = from_date.date()
    if isinstance(till_date, datetime):
        till_date = till_date.date()

    from_dt = datetime.combine(from_date, dt_time.min)
    till_dt = datetime.combine(till_date, dt_time.max)

    with SessionLocal() as session:
        rows = session.scalars(
            select(TradingDay.date).where(
                TradingDay.date >= from_dt,
                TradingDay.date <= till_dt,
                TradingDay.is_trading_day == True,
            )
        ).all()

    result = []
    for row in rows:
        if isinstance(row, datetime):
            result.append(row.date())
        else:
            result.append(row)

    return result


def is_trading_day(day: date) -> bool:
    """
    Работает ли биржа в указанную дату.
    """
    dt = datetime.combine(day, dt_time.min)

    with SessionLocal() as session:
        row = session.get(TradingDay, dt)
        return bool(row and row.is_trading_day)


# ----------------------------
# Macro
# ----------------------------

def save_macro(key_rate: float | None = None, usdrub: float | None = None, brent: float | None = None) -> None:
    """
    Сохраняем снимок макро-данных.
    """
    with SessionLocal() as session:
        session.add(
            Macro(
                ts=now_moscow(),
                key_rate=key_rate,
                usdrub=usdrub,
                brent=brent,
            )
        )
        session.commit()