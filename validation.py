from datetime import datetime, date

import pandas as pd


def validate_candles(
    df: pd.DataFrame,
    timeframe: str,
    trading_dates: list[date] | None = None,
    from_date=None,
    till_date=None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Валидация свечей перед записью в БД.

    Возвращает:
        - очищенный DataFrame,
        - список проблем/замечаний.
    """
    issues = []

    if df is None or df.empty:
        return df, issues

    df = df.copy()

    # 1. Проверка логики свечи:
    # high >= low
    # high >= max(open, close)
    # low <= min(open, close)
    mask = (
        (df["high"] >= df["low"])
        & (df["high"] >= df[["open", "close"]].max(axis=1))
        & (df["low"] <= df[["open", "close"]].min(axis=1))
    )

    bad_rows = df[~mask]

    if not bad_rows.empty:
        issues.append(
            f"Отброшено {len(bad_rows)} свечей с нарушением логики high/low/open/close."
        )
        df = df[mask]

    # 2. Проверка объёма.
    # Для дневных свечей объём должен быть больше нуля.
    # Для часовых допускаем >= 0, но отрицательные объёмы отбрасываем.
    if timeframe == "1D":
        volume_mask = df["volume"] > 0
    else:
        volume_mask = df["volume"] >= 0

    bad_volume = df[~volume_mask]

    if not bad_volume.empty:
        issues.append(
            f"Отброшено {len(bad_volume)} свечей с некорректным объёмом."
        )
        df = df[volume_mask]

    # 3. Для дневных свечей проверяем пропуски торговых дней.
    if (
        timeframe == "1D"
        and trading_dates is not None
        and from_date is not None
        and till_date is not None
    ):
        if isinstance(from_date, datetime):
            from_date = from_date.date()
        if isinstance(till_date, datetime):
            till_date = till_date.date()

        candle_dates = set(df["ts"].dt.date)

        expected_dates = {
            d for d in trading_dates
            if from_date <= d <= till_date
        }

        missing_dates = sorted(expected_dates - candle_dates)

        if missing_dates:
            issues.append(
                f"Пропущено {len(missing_dates)} торговых дней. "
                f"Примеры: {[str(d) for d in missing_dates[:10]]}"
            )

    return df, issues