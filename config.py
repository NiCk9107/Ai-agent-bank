import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "db" / "app.db"))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

TZ = ZoneInfo(TIMEZONE)


def now_moscow() -> datetime:
    """
    Возвращает текущее время в Москве как naive datetime.
    Храним в БД без таймзоны, но считаем, что это время МСК.
    """
    return datetime.now(TZ).replace(tzinfo=None)


# Список ликвидных бумаг РФ для Этапа 1.
# Это стартовый список, позже его можно расширить или загружать из индекса.
WATCHLIST = [
    "SBER", "GAZP", "LKOH", "GMKN", "ROSN", "NVTK", "TATN", "MGNT",
    "MTSS", "MOEX", "VTBR", "ALRS", "CHMF", "PHOR", "PLZL", "NLMK",
    "SNGS", "AFLT", "RUAL", "CBOM", "PIKK", "FIVE", "OZON", "YDEX",
    "HEAD", "VKCO", "TCSG", "SIBN", "HYDR", "RASP",
]