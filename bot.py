import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, WEBHOOK_URL, PORT
from database import init_db
from handlers import *
from utils import is_admin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    await init_db()
    logger.info("🚀 VETGUARD ERP v3.0 (Takomillashtirilgan) ишга тушди!")

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Барча текст киритишларни бошқаради (FSM)"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Рухсат йўқ.")
        return
    
    text = update.message.text
    action = context.user_data.get("action")
    
    # 1. Орқага қайтиш
    if text == "⬅️ Орқага":
        await start(update, context)
        return

    # 2. Агар action бўлса, унинг функциясини ишлатамиз
    if action == "add_product":
        await add_product_finish(update, context)
    elif action == "incoming":
        await incoming_quantity(update, context)
    elif action == "sell":
        if context.user_data.get("sell_payment") is None:
            await sell_payment_type(update, context)
        else:
            await sell_finish(update, context)
    elif action == "pay_debt":
        await pay_debt_finish(update, context)
    elif action == "config":
        # config_price -> config_discount ketma-ketligi
        if context.user_data.get("config_price") is None:
            await config_price(update, context)
        else:
            await config_discount(update, context)
    elif action == "add_customer":
        await add_customer_finish(update, context)
    
    # 3. Агар action топилмаса, демак бу асосий меню тугмаси
    else:
        if text == "➕ Келди":
            await incoming_start(update, context)
        elif text == "➖ Сотиш":
            await sell_start(update, context)
        elif text == "📦 Омбор қолдиғи":
            await inventory(update, context)
        elif text == "💰 Қарздорлик":
            await show_debts(update, context)
        elif text == "💸 Қарзни тўлаш":
            await pay_debt_start(update, context)
        elif text == "⚙️ Дори созлаш":
            await config_start(update, context)
        elif text == "👤 Мижозлар":
            await customers_menu(update, context)
        elif text == "🆕 Янги дори қўшиш":
            await add_product_start(update, context)
        elif text == "📜 Умумий тарих":
            await show_logs(update, context)
        elif text == "👤 Янги мижоз қўшиш":
            await add_customer_start(update, context)
        else:
            await update.message.reply_text("❌ Номаълум команда.", reply_markup=main_menu_keyboard())

def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    if WEBHOOK_URL:
        logger.info(f"🌐 Webhook: {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="/webhook",
            webhook_url=WEBHOOK_URL,
        )
    else:
        logger.info("🔄 Polling режими")
        application.run_polling()

if __name__ == "__main__":
    main()
    import requests
import base64
import os
from telegram.ext import MessageHandler, filters
from config import DEEPSEEK_API_KEY  # .env дан оламиз

# DeepSeek Vision API га сўров юбориш
async def analyze_image_with_deepseek(image_file):
    # 1. Расмни база64 га айлантирамиз
    image_bytes = await image_file.download_as_bytearray()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # 2. DeepSeek Vision API (Chat) га юбориш
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-vision",  # DeepSeek Vision модели
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Бу расмда нима ёзилган? Дори номи ва сонини топиб, JSON форматда қайтар: {'name': '...', 'quantity': ...}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    }
    response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()

# Telegram расм ҳабарларини ушловчи функция
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    
    await update.message.reply_text("📸 DeepSeek расмни таҳлил қилмоқда...")
    
    # Энг катта расмни олиш
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    # DeepSeek га юбориш
    result = await analyze_image_with_deepseek(file)
    
    # Жавобни таҳлил қилиш
    try:
        content = result["choices"][0]["message"]["content"]
        await update.message.reply_text(f"✅ DeepSeek натижаси:\n\n{content}")
        
        # Қўшимча: Агар JSON қайтса, базага ёзиш ёки сотиш мумкин!
        # ... (бу ерда SQL га ёзиш коди бўлиши мумкин)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

# bot.py даги main() ичига қўшинг:
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
