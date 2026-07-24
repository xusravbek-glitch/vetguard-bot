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
    logger.info("🚀 VETGUARD ERP v3.0 (Railway) ишга тушди!")

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Рухсат йўқ.")
        return
    
    text = update.message.text
    action = context.user_data.get("action")
    
    # Орқага қайтиш
    if text == "⬅️ Орқага":
        await start(update, context)
        return

    # Ҳар бир action га мос функцияни чақириш
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
    else:
        await update.message.reply_text("❌ Номаълум команда.", reply_markup=main_menu_keyboard())

def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Командалар
    application.add_handler(CommandHandler("start", start))
    
    # Callback (барча inline кнопкаларни битта жойда ишлайди)
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Меню кнопкалари
    application.add_handler(MessageHandler(filters.Regex("^🆕 Янги дори қўшиш$"), add_product_start))
    application.add_handler(MessageHandler(filters.Regex("^➕ Келди$"), incoming_start))
    application.add_handler(MessageHandler(filters.Regex("^➖ Сотиш$"), sell_start))
    application.add_handler(MessageHandler(filters.Regex("^📦 Омбор қолдиғи$"), inventory))
    application.add_handler(MessageHandler(filters.Regex("^💰 Қарздорлик$"), show_debts))
    application.add_handler(MessageHandler(filters.Regex("^💸 Қарзни тўлаш$"), pay_debt_start))
    application.add_handler(MessageHandler(filters.Regex("^⚙️ Дори созлаш$"), config_start))
    application.add_handler(MessageHandler(filters.Regex("^👤 Мижозлар$"), customers_menu))
    application.add_handler(MessageHandler(filters.Regex("^📜 Умумий тарих$"), show_logs))
    
    # FSM - барча текстларни ушлайди
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Ишга тушириш (авто Webhook ёки Polling)
    if WEBHOOK_URL:
        logger.info(f"Webhook режимида ишлаяпти: {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="/webhook",
            webhook_url=WEBHOOK_URL,
        )
    else:
        logger.info("Polling режимида ишлаяпти")
        application.run_polling()

if __name__ == "__main__":
    main()
