import re

import httpx


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def get_usd_rate() -> float | None:
    """
    Курс USD/RUB.
    Используется открытый сервис ЦБ РФ.
    """
    url = "https://www.cbr-xml-daily.ru/daily_json.js"

    try:
        response = httpx.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        data = response.json()
        return float(data["Valute"]["USD"]["Value"])
    except Exception:
        return None


def get_key_rate() -> float | None:
    """
    Ключевая ставка ЦБ РФ.

    Здесь используется простой парсинг страницы ЦБ.
    Если вёрстка изменится, функцию нужно будет поправить.
    """
    url = "https://www.cbr.ru/ru_key_rate/"

    try:
        response = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        response.raise_for_status()

        # Ищем значения вида "21,00%"
        matches = re.findall(r"(\d{1,2}),(\d{2})\s*%", response.text)

        if matches:
            int_part, frac_part = matches[0]
            return float(f"{int_part}.{frac_part}")

    except Exception:
        return None

    return None