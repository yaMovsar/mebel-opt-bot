import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 741468078))
WORKER_ID = int(os.getenv('WORKER_ID', 7792815764))
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен!")