import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.database import SessionLocal
from db.models import TradingDay

# Список официальных нерабочих праздничных дней РФ
# Источник: производственный календарь РФ
HOLIDAYS = [
    # 2025
    "2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05", 
    "2025-01-06", "2025-01-07", "2025-01-08",
    "2025-02-23", "2025-02-24",
    "2025-03-08", "2025-03-09",
    "2025-05-01", "2025-05-04",
    "2025-05-09", "2025-05-11",
    "2025-06-12", "2025-06-15",
    "2025-11-04",
    
    # 2026
    "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", 
    "2026-01-06", "2026-01-07", "2026-01-08",
    "2026-02-23",
    "2026-03-08",
    "2026-05-01", "2026-05-09",
    "2026-06-12",
    "2026-11-04",
]

def main():
    with SessionLocal() as s:
        updated = 0
        for date_str in HOLIDAYS:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day = s.get(TradingDay, dt)
            if day and day.is_trading_day:
                day.is_trading_day = False
                updated += 1
                print(f"  {date_str}: помечен как неторговый день")
            elif not day:
                print(f"  {date_str}: отсутствует в календаре")
        
        s.commit()
        print(f"\nОбновлено записей: {updated}")

if __name__ == "__main__":
    main()