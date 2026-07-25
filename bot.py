import logging
import requests
import base64
import os
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    filters
)
from config import BOT_TOKEN, WEBHOOK_URL, PORT, DEEPSEEK_API_KEY
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
    if text in ["⬅️ Орқага", "/start"]:
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
        if context.user_data.get("config_price") is None:
            await config_price(update, context)
        else:
            await config_discount(update, context)
    elif action == "add_customer":
        await add_customer_finish(update, context)
    
    # 3. Меню тугмалари
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

async def analyze_image_with_deepseek(image_file):
    """DeepSeek Chat/Vision API га расмни анализ қилиш"""
    try:
        image_bytes = await image_file.download_as_bytearray()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        # DeepSeek rasmiy model nomi: deepseek-chat
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": f"Суратдаги дори номи ва сонини аниқлаб беринг: data:image/jpeg;base64,{base64_image}"
                }
            ]
        }
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions", 
            headers=headers, 
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"DeepSeek API Error: {response.status_code} - {response.text}")
            return {"error": f"API Хатолик: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return {"error": str(e)}

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegram расм ҳабарларини ушловчи функция"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Рухсат йўқ.")
        return
    
    try:
        await update.message.reply_text("📸 Расм таҳлил қилинмоқда...")
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        result = await analyze_image_with_deepseek(file)
        
        if "error" in result:
            await update.message.reply_text(f"❌ Хатолик: {result['error']}")
            return
            
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        await update.message.reply_text(f"✅ Натижа:\n\n{content}")
            
    except Exception as e:
        logger.error(f"Photo handler error: {e}")
        await update.message.reply_text(f"❌ Хатолик юз берди: {e}")

def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Railway barqaror ishlashi uchun Polling rejimi tavsiya etiladi
    logger.info("🔄 Polling режимида ишга тушмоқда...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
