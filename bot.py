import logging
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    filters
)
from config import BOT_TOKEN
from database import init_db
from handlers import *
from utils import is_admin
from ai_service import process_text_with_ai, process_image_with_ai

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    await init_db()
    logger.info("🚀 VETGUARD ERP v3.0 Серверда ишга тушди!")

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Рухсат йўқ.")
        return

    text = update.message.text.strip()
    action = context.user_data.get("action")

    if text in ["⬅️ Бош менюга қайтиш", "/start"]:
        await start(update, context)
        return

    # FSM Холатлари
    if action == "add_product":
        await add_product_finish(update, context)
    elif action == "incoming":
        await incoming_quantity(update, context)
    elif action == "sell":
        if "sell_quantity" not in context.user_data:
            await sell_quantity(update, context)
        elif "sell_discount" not in context.user_data:
            await sell_discount(update, context)
        else:
            await sell_finish(update, context)
    elif action == "pay_debt":
        await pay_debt_finish(update, context)
    elif action == "config":
        if "config_price" not in context.user_data:
            await config_price(update, context)
        else:
            await config_discount(update, context)
    elif action == "add_customer":
        await add_customer_finish(update, context)

    # Асосий меню тугмалари
    elif text == "🛒 Сотув қилиш":
        await sell_start(update, context)
    elif text == "📥 Омборга кирим":
        await incoming_start(update, context)
    elif text == "📦 Омбор қолдиғи":
        await inventory(update, context)
    elif text == "💰 Қарздорлар рўйхати":
        await show_debts(update, context)
    elif text == "💸 Қарзни узиш":
        await pay_debt_start(update, context)
    elif text == "🏷 Дори нарх/скидка созлаш":
        await config_start(update, context)
    elif text == "➕ Янги дори қўшиш":
        await add_product_start(update, context)
    elif text == "👤 Мижозлар бўлими":
        await customers_menu(update, context)
    elif text == "📋 Барча мижозлар":
        await list_customers(update, context)
    elif text == "👤 Янги мижоз қўшиш":
        await add_customer_start(update, context)
    elif text == "📜 Сотувлар тарихи":
        await show_logs(update, context)

    # Стандарт бўлмаган матнлар -> AI орқали ҳисоблаш
    else:
        await update.message.reply_text("🤖 *AI таҳлил қилмоқда...*", parse_mode="Markdown")
        ai_data = await process_text_with_ai(text)
        await process_ai_action(update, context, ai_data)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Рухсат йўқ.")
        return

    try:
        await update.message.reply_text("📸 *AI расмни ўқиб таҳлил қилмоқда...*", parse_mode="Markdown")
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        ai_data = await process_image_with_ai(image_bytes)
        await process_ai_action(update, context, ai_data)
    except Exception as e:
        logger.error(f"Photo error: {e}")
        await update.message.reply_text("❌ Расмни таҳлил қилишда хатолик бўлди.")

def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logger.info("🔄 Polling режимида ишга тушмоқда...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
