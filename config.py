# config.py
import os
from dotenv import load_dotenv

load_dotenv("token.env")  # читает .env файл

# База данных
DB_PATH = "data/kaspi_tracker.db"

# Telegram — берём из .env, не из кода
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Как часто проверять цены (в часах)
CHECK_INTERVAL = 6