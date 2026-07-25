from config import ADMIN_IDS

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def check_admin(update, context) -> bool:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Бу ботдан фақат администратор фойдаланиши мумкин.")
        return False
    return True

def format_currency(amount: float) -> str:
    return f"{amount:,.0f}".replace(",", " ") + " сўм"

async def clear_user_data(context):
    context.user_data.clear()
