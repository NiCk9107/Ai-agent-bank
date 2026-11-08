# Stock Agent RF

Проект ИИ-агента для фондового рынка РФ.

Текущий этап: Этап 1 — сбор и хранение данных.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env

# первичная загрузка дневных свечей
python scripts/initial_load.py --timeframes 1D

# при желании загрузить ещё и часовые
python scripts/initial_load.py --timeframes 1D,1H

# запуск планировщика
python scheduler.py