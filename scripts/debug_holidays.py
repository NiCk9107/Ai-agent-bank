import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.database import SessionLocal
from db.models import TradingDay

with SessionLocal() as s:
    # Ищем дни, помеченные как НЕ торговые
    non_trading = s.query(TradingDay).filter(TradingDay.is_trading_day == False).all()
    
    print(f"Всего дней в календаре: {s.query(TradingDay).count()}")
    print(f"Дней с is_trading_day=False: {len(non_trading)}")
    
    if non_trading:
        print("\nПримеры неторговых дней:")
        for day in non_trading[:10]:
            print(f"  {day.date.strftime('%Y-%m-%d %A')}")
    else:
        print("\n⚠ ВСЕ дни помечены как торговые — праздники не отмечены!")
        
        # Проверяем конкретные праздники
        print("\nПроверка известных праздников:")
        test_dates = [
            "2025-01-01", "2025-01-07", "2025-05-09", "2025-06-12",
            "2026-01-01", "2026-01-07", "2026-05-09", "2026-06-12"
        ]
        for date_str in test_dates:
            from datetime import datetime
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day = s.get(TradingDay, dt)
            if day:
                print(f"  {date_str}: is_trading_day={day.is_trading_day}")
            else:
                print(f"  {date_str}: НЕТ В КАЛЕНДАРЕ")