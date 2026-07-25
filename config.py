import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", 5000))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "")

# SQLAlchemy + asyncpg uchun URL ni avtomatik to'g'риlash
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Admin settings
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# Bot settings
LOW_STOCK_LIMIT = int(os.getenv("LOW_STOCK_LIMIT", 5))

# Validation
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN қўйилмаган!")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL қўйилмаган!")
if not ADMIN_IDS:
    raise ValueError("❌ ADMIN_IDS қўйилмаган!")
