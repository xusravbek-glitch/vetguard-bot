from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS

def format_currency(amount):
    return f"{amount:,.0f} сўм"

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Рухсат йўқ.")
        return False
    return True

async def clear_user_data(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
