from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from database import get_all_products, get_all_customers
import logging

logger = logging.getLogger(__name__)

def main_menu_keyboard():
    """Асосий меню тугмалари"""
    keyboard = [
        [KeyboardButton("➕ Келди"), KeyboardButton("➖ Сотиш")],
        [KeyboardButton("📦 Омбор қолдиғи"), KeyboardButton("💰 Қарздорлик")],
        [KeyboardButton("💸 Қарзни тўлаш"), KeyboardButton("⚙️ Дори созлаш")],
        [KeyboardButton("👤 Мижозлар"), KeyboardButton("🆕 Янги дори қўшиш")],
        [KeyboardButton("📜 Умумий тарих"), KeyboardButton("👤 Янги мижоз қўшиш")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def back_keyboard():
    """Орқага қайтиш тугмаси"""
    keyboard = [[KeyboardButton("⬅️ Орқага")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def payment_keyboard():
    """Тўлов турини танлаш тугмалари"""
    keyboard = [[KeyboardButton("💵 Нақд"), KeyboardButton("💳 Насия")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def customer_menu_keyboard():
    """Мижозлар меню"""
    keyboard = [
        [KeyboardButton("👤 Мижозлар рўйхати")],
        [KeyboardButton("🆕 Янги мижоз")],
        [KeyboardButton("⬅️ Орқага")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def product_inline_keyboard():
    """Дорилар инлайн клавиатураси"""
    try:
        products = await get_all_products()
        if not products:
            return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Дорилар йўқ", callback_data="none")]])
        
        keyboard = []
        for product in products:
            keyboard.append([InlineKeyboardButton(f"📦 {product.name}", callback_data=f"prod_{product.name}")])
        keyboard.append([InlineKeyboardButton("⬅️ Орқага", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"❌ product_inline_keyboard xatosi: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Хатолик", callback_data="none")]])

async def customer_inline_keyboard():
    """Мижозлар инлайн клавиатураси"""
    try:
        customers = await get_all_customers()
        if not customers:
            return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Мижозлар йўқ", callback_data="none")]])
        
        keyboard = []
        for customer in customers:
            keyboard.append([InlineKeyboardButton(f"👤 {customer.name}", callback_data=f"cust_{customer.name}")])
        keyboard.append([InlineKeyboardButton("⬅️ Орқага", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"❌ customer_inline_keyboard xatosi: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Хатолик", callback_data="none")]])