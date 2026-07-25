import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Asyncpg учун DATABASE_URL ни автоматик форматлаш
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
LOW_STOCK_LIMIT = int(os.getenv("LOW_STOCK_LIMIT", 5))

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN муҳит ўзгарувчиси қўйилмаган!")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL муҳит ўзгарувчиси қўйилмаган!")
if not ADMIN_IDS:
    raise ValueError("❌ ADMIN_IDS муҳит ўзгарувчиси қўйилмаган!")
