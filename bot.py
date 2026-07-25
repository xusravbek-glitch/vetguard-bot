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
from handlers import (
    start,
    add_product_finish,
    incoming_quantity,
    sell_quantity,
    sell_discount,
    sell_finish,
    pay_debt_finish,
    config_price,
    config_discount,
    add_customer_finish,
    sell_start,
    incoming_start,
    inventory,
    show_debts,
    pay_debt_start,
    config_start,
    add_product_start,
    customers_menu,
    list_customers,
    add_customer_start,
    show_logs,
    handle_callback,
    process_ai_action,
    handle_search_text
)
from utils import is_admin
from ai_service import process_text_with_ai, process_image_with_ai

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    await init_db()
    logger.info("🚀 VETGUARD ERP v3.0 Серверда муваффақиятли ишга тушди!")

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Бу ботдан фойдаланиш учун сизга рухсат берилмаган.")
        return

    text = update.message.text.strip()
    action = context.user_data.get("action")

    if text in ["⬅️ Бош менюга қайтиш", "/start"]:
        context.user_data.clear()
        await start(update, context)
        return

    if text == "🛒 Сотув қилиш":
        context.user_data.clear()
        await sell_start(update, context)
        return
    elif text == "📥 Омборга кирим":
        context.user_data.clear()
        await incoming_start(update, context)
        return
    elif text == "📦 Омбор қолдиғи":
        await inventory(update, context)
        return
    elif text == "💰 Қарздорлар рўйхати":
        await show_debts(update, context)
        return
    elif text == "💸 Қарзни узиш":
        context.user_data.clear()
        await pay_debt_start(update, context)
        return
    elif text == "🏷 Дори нарх/скидка созлаш":
        context.user_data.clear()
        await config_start(update, context)
        return
    elif text == "➕ Янги дори қўшиш":
        context.user_data.clear()
        await add_product_start(update, context)
        return
    elif text == "👤 Мижозлар бўлими":
        await customers_menu(update, context)
        return
    elif text == "📋 Барча мижозлар":
        await list_customers(update, context)
        return
    elif text == "👤 Янги мижоз қўшиш":
        context.user_data.clear()
        await add_customer_start(update, context)
        return
    elif text == "📜 Сотувлар тарихи":
        await show_logs(update, context)
        return

    # Дори қидириш ҳолатлари
    if action in ["search_incoming_product", "search_sell_product", "config"]:
        await handle_search_text(update, context)
        return

    # Бошқа FSM ҳолатлари
    elif action == "add_product":
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
    elif action == "config_await_price":
        await config_price(update, context)
    elif action == "config_await_discount":
        await config_discount(update, context)
    elif action == "add_customer":
        await add_customer_finish(update, context)

    # Эркин матнлар -> AI таҳлил
    else:
        status_msg = await update.message.reply_text("🤖 *AI таҳлил қилмоқда...*", parse_mode="Markdown")
        try:
            ai_data = await process_text_with_ai(text)
            await process_ai_action(update, context, ai_data)
        except Exception as e:
            logger.error(f"AI Text Error: {e}")
            await update.message.reply_text("❌ Маълумотни қайта ишлашда хатолик бўлди.")
        finally:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
            except Exception:
                pass

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Бу ботдан фойдаланиш учун сизга рухсат берилмаган.")
        return

    status_msg = await update.message.reply_text("📸 *AI расмни (накладнаяни) ўқиб таҳлил қилмоқда...*", parse_mode="Markdown")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        ai_data = await process_image_with_ai(image_bytes)
        await process_ai_action(update, context, ai_data)
    except Exception as e:
        logger.error(f"Photo processing error: {e}")
        await update.message.reply_text("❌ Накладная суратини таҳлил қилишда хатолик юз берди.")
    finally:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        except Exception:
            pass

def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logger.info("🔄 Polling режимида бот ишга тушмоқда...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
