# Weather Telegram Bot

Бот для получения текущей погоды и прогноза на 5 дней в любом городе.

## Функционал
- Текущая погода по названию города или геолокации
- Прогноз на 5 дней
- Поддержка русского языка

## Технологии
- Python 3
- Telebot (python-telegram-bot)
- OpenWeatherMap API

## Установка
1. Клонировать репозиторий
2. Установить зависимости: `pip install -r requirements.txt`
3. Создать файл config.py с вашими токенами:
```python
TOKEN = "your_telegram_bot_token"
OPENWEATHER_TOKEN = "your_openweather_token"
