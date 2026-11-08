import sqlite3

conn = sqlite3.connect("db/app.db")

print("Всего свечей:            ", conn.execute("SELECT COUNT(*) FROM candles").fetchone()[0])
print("SBER по таймфреймам:     ", conn.execute("SELECT timeframe, COUNT(*) FROM candles WHERE ticker='SBER' GROUP BY timeframe").fetchall())
print("Диапазон дат SBER 1D:    ", conn.execute("SELECT MIN(ts), MAX(ts) FROM candles WHERE ticker='SBER' AND timeframe='1D'").fetchall())
print("Строк в календаре:       ", conn.execute("SELECT COUNT(*) FROM trading_calendar").fetchone()[0])
print("Из них торговых дней:    ", conn.execute("SELECT COUNT(*) FROM trading_calendar WHERE is_trading_day=1").fetchone()[0])
print("Последние события:")
for row in conn.execute("SELECT ts, type, payload FROM events ORDER BY id DESC LIMIT 10"):
    print("  ", row)