import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analytics.screener import screen_oversold_in_uptrend


def main():
    print("Скринер: RSI(14) < 30 и цена выше SMA200")
    rows = screen_oversold_in_uptrend()
    if not rows:
        print("Сегодня кандидатов нет. Это нормально: правило строгое.")
        return
    print(f"{'Тикер':<8}{'Дата':<12}{'Цена':>10}{'RSI14':>8}{'SMA200':>10}")
    for r in rows:
        print(f"{r['ticker']:<8}{str(r['date']):<12}{r['close']:>10}{r['rsi14']:>8}{r['sma200']:>10}")


if __name__ == "__main__":
    main()