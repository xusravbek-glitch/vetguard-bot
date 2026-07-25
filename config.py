import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", 5000))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/vetguard")

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Admin settings
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# Bot settings
LOW_STOCK_LIMIT = int(os.getenv("LOW_STOCK_LIMIT", 5))

# Webhook URL ni to'g'ri formatda olish
if WEBHOOK_URL and not WEBHOOK_URL.endswith("/webhook"):
    WEBHOOK_URL = WEBHOOK_URL.rstrip("/") + "/webhook"

# Validation
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN қўйилмаган!")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL қўйилмаган!")
if not ADMIN_IDS:
    raise ValueError("❌ ADMIN_IDS қўйилмаган!")
