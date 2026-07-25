from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS
import logging

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Фойдаланувчи админ эканини текшириш"""
    return user_id in ADMIN_IDS

async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Админни асинк текшириш"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Рухсат йўқ. Фақат админлар бу командани ишлата олади.")
        return False
    return True

def format_currency(amount: float) -> str:
    """Пулни форматлаш (сўм)"""
    return f"{amount:,.0f} сўм"

async def clear_user_data(context: ContextTypes.DEFAULT_TYPE):
    """Фойдаланувчи маълумотларини тозалаш"""
    context.user_data.clear()

def get_emoji_by_quantity(quantity: int, low_stock_limit: int = 5) -> str:
    """Миқдор бўйича эмодзи ола"""
    if quantity <= 0:
        return "❌"
    elif quantity <= low_stock_limit:
        return "🔴"
    else:
        return "🟢"
