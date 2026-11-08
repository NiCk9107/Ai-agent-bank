import time
from datetime import date

import httpx
import pandas as pd


ISS_BASE = "https://iss.moex.com/iss"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def _get_json(url: str, params: dict):
    response = httpx.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_candles(
    ticker: str,
    interval: int,
    from_date,
    till_date,
) -> pd.DataFrame:
    """
    Загружает свечи из ISS MOEX.

    interval:
        24 = дневные свечи
        60 = часовые свечи
    """
    url = f"{ISS_BASE}/engines/stock/markets/shares/securities/{ticker}/candles.json"

    all_rows = []
    start = 0

    while True:
        params = {
            "from": str(from_date),
            "till": str(till_date),
            "interval": interval,
            "iss.meta": "off",
            "iss.only": "candles",
            "candles.columns": "open,close,high,low,value,volume,begin,end",
            "start": start,
        }

        data = _get_json(url, params)
        block = data.get("candles", {})
        rows = block.get("data", [])

        if not rows:
            break

        all_rows.extend(rows)

        # ISS обычно отдаёт до 500 свечей за раз
        if len(rows) < 500:
            break

        start += len(rows)
        time.sleep(0.4)

    if not all_rows:
        return pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])

    columns = ["open", "close", "high", "low", "value", "volume", "begin", "end"]
    df = pd.DataFrame(all_rows, columns=columns)

    df["ts"] = pd.to_datetime(df["begin"])

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["volume"] = (
        pd.to_numeric(df["volume"], errors="coerce")
        .fillna(0)
        .astype("int64")
    )

    df = df[["ts", "open", "high", "low", "close", "volume"]]
    df = df.dropna(subset=["open", "high", "low", "close"])

    return df


def fetch_security_info(ticker: str) -> dict:
    """
    Базовая информация по бумаге.
    """
    url = f"{ISS_BASE}/securities/{ticker}.json"

    try:
        data = _get_json(url, {"iss.meta": "off"})

        description = data.get("description", {})
        columns = description.get("columns", [])
        rows = description.get("data", [])

        if not rows:
            return {}

        row = dict(zip(columns, rows[0]))

        return {
            "name": row.get("name"),
            "lot_size": row.get("lotsize"),
            "sector": row.get("sectorid"),
        }

    except Exception:
        return {}


def fetch_trading_calendar(from_date, till_date) -> pd.DataFrame:
    """
    Торговый календарь Мосбиржи (борд TQBR).
    """
    url = f"{ISS_BASE}/engines/stock/markets/shares/boards/TQBR/tradingdays.json"

    rows = []
    start = 0

    while True:
        params = {
            "from": str(from_date),
            "till": str(till_date),
            "start": start,
            "iss.meta": "off",
            "iss.only": "tradingdays",
        }

        data = _get_json(url, params)
        block = data.get("tradingdays") or {}
        cols = block.get("columns", [])
        batch = block.get("data", [])

        if not batch:
            break

        rows.extend(batch)

        if len(batch) < 500:
            break

        start += len(batch)
        time.sleep(0.3)

    if not rows:
        # Запасной вариант: календарь из дневных свечей индекса IMOEX
        return _calendar_from_index(from_date, till_date)

    df = pd.DataFrame(rows, columns=cols)

    # Названия колонок могут отличаться — нормализуем
    date_col = next((c for c in ("trade_date", "date") if c in df.columns), df.columns[0])
    flag_col = next((c for c in ("is_trading_day",) if c in df.columns), df.columns[1])

    df = df[[date_col, flag_col]].rename(
        columns={date_col: "date", flag_col: "is_trading_day"}
    )
    df["date"] = pd.to_datetime(df["date"])
    df["is_trading_day"] = df["is_trading_day"].astype(int).astype(bool)

    return df[["date", "is_trading_day"]]


def _calendar_from_index(from_date, till_date) -> pd.DataFrame:
    """
    Фолбэк: торговыми считаем дни, когда есть дневные свечи индекса IMOEX.
    """
    url = f"{ISS_BASE}/engines/stock/markets/index/securities/IMOEX/candles.json"

    rows = []
    start = 0
    data = {}

    while True:
        params = {
            "from": str(from_date),
            "till": str(till_date),
            "interval": 24,
            "start": start,
            "iss.meta": "off",
            "iss.only": "candles",
        }
        data = _get_json(url, params)
        batch = data.get("candles", {}).get("data", [])

        if not batch:
            break

        rows.extend(batch)

        if len(batch) < 500:
            break

        start += len(batch)
        time.sleep(0.3)

    if not rows:
        return pd.DataFrame(columns=["date", "is_trading_day"])

    cols = data.get("candles", {}).get("columns", [])
    df = pd.DataFrame(rows, columns=cols)

    dates = pd.to_datetime(df["begin"]).dt.normalize().unique()
    out = pd.DataFrame({"date": dates, "is_trading_day": True})
    return out.sort_values("date").reset_index(drop=True)