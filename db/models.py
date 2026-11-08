from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Float,
    DateTime,
    Boolean,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Security(Base):
    __tablename__ = "securities"

    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(100))
    lot_size: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Candle(Base):
    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    timeframe: Mapped[str] = mapped_column(String(10), index=True)  # 1D / 1H
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)

    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(BigInteger)

    __table_args__ = (
        UniqueConstraint("ticker", "timeframe", "ts", name="uq_candle"),
    )


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    timeframe: Mapped[str] = mapped_column(String(10), default="1D")
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)

    rsi14: Mapped[float | None] = mapped_column(Float)
    macd: Mapped[float | None] = mapped_column(Float)
    sma50: Mapped[float | None] = mapped_column(Float)
    sma200: Mapped[float | None] = mapped_column(Float)
    atr14: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("ticker", "timeframe", "ts", name="uq_indicator"),
    )


class News(Base):
    __tablename__ = "news"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    source: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text)
    text: Mapped[str | None] = mapped_column(Text)
    tickers: Mapped[str | None] = mapped_column(Text)  # JSON-список тикеров
    sentiment: Mapped[str | None] = mapped_column(String(20))
    llm_summary: Mapped[str | None] = mapped_column(Text)


class Fundamental(Base):
    __tablename__ = "fundamentals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    period: Mapped[str] = mapped_column(String(20))

    revenue: Mapped[float | None] = mapped_column(Float)
    net_profit: Mapped[float | None] = mapped_column(Float)
    debt: Mapped[float | None] = mapped_column(Float)
    pe: Mapped[float | None] = mapped_column(Float)
    dividend_yield: Mapped[float | None] = mapped_column(Float)


class Dividend(Base):
    __tablename__ = "dividends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    ex_date: Mapped[datetime | None] = mapped_column(DateTime)
    amount: Mapped[float | None] = mapped_column(Float)
    yield_pct: Mapped[float | None] = mapped_column(Float)


class Macro(Base):
    __tablename__ = "macro"

    ts: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    key_rate: Mapped[float | None] = mapped_column(Float)
    usdrub: Mapped[float | None] = mapped_column(Float)
    brent: Mapped[float | None] = mapped_column(Float)


class Signal(Base):
    __tablename__ = "signals"

    signal_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    ticker: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(10))  # long / short / watch
    strength: Mapped[float] = mapped_column(Float)
    horizon: Mapped[str | None] = mapped_column(String(30))

    price_at_signal: Mapped[float | None] = mapped_column(Float)
    stop_loss: Mapped[float | None] = mapped_column(Float)
    take_profit: Mapped[float | None] = mapped_column(Float)
    position_size_pct: Mapped[float | None] = mapped_column(Float)

    triggers: Mapped[str | None] = mapped_column(Text)   # JSON-список фактов
    context: Mapped[str | None] = mapped_column(Text)    # JSON-контекст

    status: Mapped[str] = mapped_column(String(20), default="active")
    exit_price: Mapped[float | None] = mapped_column(Float)
    pnl: Mapped[float | None] = mapped_column(Float)


class PaperPosition(Base):
    __tablename__ = "paper_portfolio"

    position_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    qty: Mapped[int] = mapped_column(Integer)
    entry: Mapped[float] = mapped_column(Float)
    stop: Mapped[float | None] = mapped_column(Float)
    tp: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="open")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    type: Mapped[str] = mapped_column(String(50), index=True)
    payload: Mapped[str | None] = mapped_column(Text)


class ApiCache(Base):
    __tablename__ = "api_cache"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    response_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class TradingDay(Base):
    """
    Торговый календарь Мосбиржи.
    """
    __tablename__ = "trading_calendar"

    date: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    is_trading_day: Mapped[bool] = mapped_column(Boolean)