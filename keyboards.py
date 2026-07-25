from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from database import get_all_products, get_all_customers
import logging

logger = logging.getLogger(__name__)

def main_menu_keyboard():
    """ Янгиланган ва оқилона тақсимланган асосий меню """
    keyboard = [
        [KeyboardButton("🛒 Сотув қилиш"), KeyboardButton("📥 Омборга кирим")],
        [KeyboardButton("📦 Омбор қолдиғи"), KeyboardButton("💰 Қарздорлар рўйхати")],
        [KeyboardButton("💸 Қарзни узиш"), KeyboardButton("🏷 Дори нарх/скидка созлаш")],
        [KeyboardButton("➕ Янги дори қўшиш"), KeyboardButton("👤 Мижозлар бўлими")],
        [KeyboardButton("📜 Сотувлар тарихи")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def back_keyboard():
    keyboard = [[KeyboardButton("⬅️ Бош менюга қайтиш")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def payment_keyboard():
    keyboard = [
        [KeyboardButton("💵 Нақд тўлов"), KeyboardButton("💳 Насия (Қарзга)")],
        [KeyboardButton("⬅️ Бош менюга қайтиш")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def customer_menu_keyboard():
    keyboard = [
        [KeyboardButton("📋 Барча мижозлар"), KeyboardButton("👤 Янги мижоз қўшиш")],
        [KeyboardButton("⬅️ Бош менюга қайтиш")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def product_inline_keyboard():
    try:
        products = await get_all_products()
        if not products:
            return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Дорилар топилмади", callback_data="none")]])
        
        keyboard = []
        for p in products:
            keyboard.append([InlineKeyboardButton(f"💊 {p.name} ({p.quantity} шт | {int(p.price)} сўм)", callback_data=f"prod_{p.name}")])
        keyboard.append([InlineKeyboardButton("❌ Бекор қилиш", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"product_inline_keyboard error: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Хатолик", callback_data="none")]])

async def customer_inline_keyboard():
    try:
        customers = await get_all_customers()
        if not customers:
            return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Мижозлар йўқ", callback_data="none")]])
        
        keyboard = []
        for c in customers:
            keyboard.append([InlineKeyboardButton(f"👤 {c.name}", callback_data=f"cust_{c.name}")])
        keyboard.append([InlineKeyboardButton("❌ Бекор қилиш", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"customer_inline_keyboard error: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Хатолик", callback_data="none")]])
