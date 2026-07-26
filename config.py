import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Қолдиғи кам қолган товарлар учун лимит (Хатолик чиқмаслиги учун қўшилди)
LOW_STOCK_LIMIT = int(os.getenv("LOW_STOCK_LIMIT", 5))

admin_ids_str = os.getenv("ADMIN_IDS", "")
try:
    ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_str.split(",") if admin_id.strip()]
except ValueError:
    ADMIN_IDS = []

if not BOT_TOKEN:
    raise ValueError("❌ ХАТО: BOT_TOKEN топилмади!")

if not GEMINI_API_KEY:
    raise ValueError("❌ ХАТО: GEMINI_API_KEY топилмади!")
