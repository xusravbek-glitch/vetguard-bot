from telegram import Update
from telegram.ext import ContextTypes
from database import *
from keyboards import *
from utils import *
from config import LOW_STOCK_LIMIT
import logging

logger = logging.getLogger(__name__)

# ==========================
# START
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    await clear_user_data(context)
    await update.message.reply_text(
        "📦 **VETGUARD ERP v3.0 (PostgreSQL)**",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )

# ==========================
# 1. ЯНГИ ДОРИ ҚЎШИШ
# ==========================
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    context.user_data["action"] = "add_product"
    await update.message.reply_text("🆕 Янги дори номини киритинг:", reply_markup=back_keyboard())

async def add_product_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = update.message.text.strip()
        if not name:
            await update.message.reply_text("❌ Ном бўш бўлмасин.", reply_markup=back_keyboard())
            return
        existing = await get_product(name)
        if existing:
            await update.message.reply_text(f"❌ {name} аллақачон бор.")
            await start(update, context)
            return
        await add_product(name)
        await update.message.reply_text(f"✅ {name} қўшилди.", reply_markup=main_menu_keyboard())
        context.user_data.clear()
    except Exception as e:
        logger.error(f"add_product_finish error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")
        await start(update, context)

# ==========================
# 2. КЕЛИШ
# ==========================
async def incoming_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    context.user_data["action"] = "incoming"
    await update.message.reply_text("Дорини танланг:", reply_markup=await product_inline_keyboard())

async def incoming_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.text.isdigit():
            await update.message.reply_text("❌ Сон киритинг.", reply_markup=back_keyboard())
            return
        quantity = int(update.message.text)
        if quantity <= 0:
            await update.message.reply_text("❌ Миқдор 0 дан катта бўлиши керак.", reply_markup=back_keyboard())
            return
            
        product_name = context.user_data.get("incoming_product")
        if not product_name:
            await update.message.reply_text("❌ Дори танланмаган.", reply_markup=main_menu_keyboard())
            context.user_data.clear()
            return
            
        product = await get_product(product_name)
        if not product:
            await update.message.reply_text(f"❌ {product_name} топилмади.")
            await start(update, context)
            return
            
        await update_product_quantity(product_name, product.quantity + quantity)
        await update.message.reply_text(
            f"✅ {product_name} миқдори {quantity} донага ошди.", 
            reply_markup=main_menu_keyboard()
        )
        context.user_data.clear()
    except Exception as e:
        logger.error(f"incoming_quantity error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")
        await start(update, context)

# ==========================
# 3. СОТИШ
# ==========================
async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    context.user_data["action"] = "sell"
    await update.message.reply_text("Дорини танланг:", reply_markup=await product_inline_keyboard())

async def sell_payment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        payment = update.message.text
        if payment not in ["💵 Нақд", "💳 Насия"]:
            await update.message.reply_text("❌ Нотўғри танлов. Тугмалардан бирини босинг.")
            return
        context.user_data["sell_payment"] = payment
        product_name = context.user_data.get("sell_product")
        if not product_name:
            await update.message.reply_text("❌ Дори танланмаган.")
            await start(update, context)
            return
        product = await get_product(product_name)
        if not product:
            await update.message.reply_text(f"❌ {product_name} топилмади.")
            await start(update, context)
            return
        final_price = product.price * (1 - product.discount / 100)
        context.user_data["sell_final_price"] = final_price
        await update.message.reply_text(
            f"💵 {product_name} нархи: {format_currency(final_price)} (чегирма {product.discount}%)\nМиқдорини киритинг:", 
            reply_markup=back_keyboard()
        )
    except Exception as e:
        logger.error(f"sell_payment_type error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")
        await start(update, context)

async def sell_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.text.isdigit():
            await update.message.reply_text("❌ Сон киритинг.")
            return
        quantity = int(update.message.text)
        if quantity <= 0:
            await update.message.reply_text("❌ Миқдор 0 дан катта бўлиши керак.")
            return
        
        product_name = context.user_data.get("sell_product")
        customer = context.user_data.get("sell_customer")
        payment_type = context.user_data.get("sell_payment")
        final_price = context.user_data.get("sell_final_price")
        
        if not all([product_name, customer, payment_type, final_price]):
            await update.message.reply_text("❌ Савдо маълумотлари тўлиқ эмас. Қайтадан бошланг.")
            await start(update, context)
            return

        product = await get_product(product_name)
        if not product or product.quantity < quantity:
            available = product.quantity if product else 0
            await update.message.reply_text(f"❌ Омборда {available} дона бор.")
            return
        
        total = int(final_price * quantity)
        new_quantity = product.quantity - quantity
        await update_product_quantity(product_name, new_quantity)
        
        if payment_type == "💳 Насия":
            debt = await get_debt(customer)
            current_debt = debt.amount if debt else 0
            await update_debt(customer, current_debt + total)
            
        await log_sale(customer, product_name, quantity, total, payment_type)
        await update.message.reply_text(
            f"✅ Сотилди: {product_name} x{quantity}\n💰 {format_currency(total)}\n📦 Қолди: {new_quantity}", 
            reply_markup=main_menu_keyboard()
        )
        if new_quantity <= LOW_STOCK_LIMIT:
            await update.message.reply_text(f"⚠️ **{product_name}** тугаяпти! {new_quantity} дона қолди.", parse_mode="Markdown")
        context.user_data.clear()
    except Exception as e:
        logger.error(f"sell_finish error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")
        await start(update, context)

# ==========================
# 4. ҚАРЗНИ ТЎЛАШ
# ==========================
async def pay_debt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    context.user_data["action"] = "pay_debt"
    await update.message.reply_text("Мижозни танланг:", reply_markup=await customer_inline_keyboard())

async def pay_debt_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.text.isdigit():
            await update.message.reply_text("❌ Сумма киритинг.")
            return
        amount = int(update.message.text)
        if amount <= 0:
            await update.message.reply_text("❌ Сумма нотўғри.")
            return
        customer = context.user_data.get("pay_debt_customer")
        if not customer:
            await update.message.reply_text("❌ Мижоз танланмаган.")
            await start(update, context)
            return
        debt = await get_debt(customer)
        current_debt = debt.amount if debt else 0
        if amount > current_debt:
            await update.message.reply_text(f"❌ Қарздан ортиқ тўлайсиз. Қарз: {format_currency(current_debt)}")
            return
        new_amount = current_debt - amount
        await update_debt(customer, new_amount)
        await update.message.reply_text(f"✅ Тўланди. Қолган қарз: {format_currency(new_amount)}", reply_markup=main_menu_keyboard())
        context.user_data.clear()
    except Exception as e:
        logger.error(f"pay_debt_finish error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")
        await start(update, context)

# ==========================
# 5. ДОРИ СОЗЛАШ
# ==========================
async def config_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    context.user_data["action"] = "config"
    await update.message.reply_text("Дорини танланг:", reply_markup=await product_inline_keyboard())

async def config_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.text.isdigit():
            await update.message.reply_text("❌ Нархни сон киритинг.", reply_markup=back_keyboard())
            return
        context.user_data["config_price"] = int(update.message.text)
        await update.message.reply_text("Чегирма фоизини киритинг (0-99):", reply_markup=back_keyboard())
    except Exception as e:
        logger.error(f"config_price error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")

async def config_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.text.isdigit():
            await update.message.reply_text("❌ Фоизни сон киритинг.", reply_markup=back_keyboard())
            return
        discount = int(update.message.text)
        if discount < 0 or discount > 99:
            await update.message.reply_text("❌ Фоиз 0-99 оралиғида бўлиши керак.")
            return
        product_name = context.user_data.get("config_product")
        price = context.user_data.get("config_price")
        if not product_name or price is None:
            await update.message.reply_text("❌ Маълумотлар тўлиқ эмас.")
            await start(update, context)
            return
        await update_product_details(product_name, price, discount)
        await update.message.reply_text(f"✅ {product_name} янгиланди:\n💰 {format_currency(price)}\n🎁 {discount}% чегирма", reply_markup=main_menu_keyboard())
        context.user_data.clear()
    except Exception as e:
        logger.error(f"config_discount error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")
        await start(update, context)

# ==========================
# 6. МИЖОЗЛАР
# ==========================
async def customers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    await update.message.reply_text("Мижозларни бошқариш:", reply_markup=customer_menu_keyboard())

async def add_customer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    context.user_data["action"] = "add_customer"
    await update.message.reply_text("Янги мижоз исми:", reply_markup=back_keyboard())

async def add_customer_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = update.message.text.strip()
        if not name:
            await update.message.reply_text("❌ Исм бўш бўлмасин.", reply_markup=back_keyboard())
            return
        customers = await get_all_customers()
        if any(c.name == name for c in customers):
            await update.message.reply_text(f"❌ {name} аллақачон бор.")
            await start(update, context)
            return
        await add_customer(name)
        await update.message.reply_text(f"✅ {name} мижозлар рўйхатига қўшилди.", reply_markup=main_menu_keyboard())
        context.user_data.clear()
    except Exception as e:
        logger.error(f"add_customer_finish error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")
        await start(update, context)

# ==========================
# 7. СТАТИК МЕНЮЛАР
# ==========================
async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await check_admin(update, context):
            return
        products = await get_all_products()
        if not products:
            await update.message.reply_text("📦 Омбор бўш.")
            return
        lines = ["📦 **Омбор ҳолати:**\n"]
        for p in products:
            status = "🔴" if p.quantity <= LOW_STOCK_LIMIT else "🟢"
            lines.append(f"{status} **{p.name}**")
            lines.append(f"   📦 {p.quantity} дона")
            lines.append(f"   💰 {format_currency(p.price)}")
            lines.append(f"   🎁 {p.discount}% чегирма\n")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"inventory error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")

async def show_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await check_admin(update, context):
            return
        debts = await get_all_debts()
        if not debts:
            await update.message.reply_text("Қарз йўқ.")
            return
        lines = ["💰 **Қарздорлик:**\n"]
        for d in debts:
            if d.amount > 0:
                lines.append(f"👤 {d.customer_name}: {format_currency(d.amount)}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"show_debts error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await check_admin(update, context):
            return
        logs = await get_sale_logs()
        if not logs:
            await update.message.reply_text("Тарих бўш.")
            return
        lines = ["📜 **Сўнгги 100 та операция:**\n"]
        for log in logs:
            lines.append(f"[{log.timestamp}] {log.payment_type}: {log.customer} → {log.product} x{log.quantity} = {format_currency(log.total)}")
        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:4000] + "\n... (давоми бор)"
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"show_logs error: {e}")
        await update.message.reply_text(f"❌ Хатолик: {e}")

# ==========================
# CALLBACK HANDLER
# ==========================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_main":
        await start(update, context)
        return

    action = context.user_data.get("action")
    
    if action == "incoming":
        if query.data.startswith("prod_"):
            product = query.data.replace("prod_", "")
            context.user_data["incoming_product"] = product
            await query.message.reply_text(f"📥 {product} миқдорини киритинг:", reply_markup=back_keyboard())
            
    elif action == "sell":
        if query.data.startswith("prod_"):
            context.user_data["sell_product"] = query.data.replace("prod_", "")
            await query.message.reply_text("👤 Мижозни танланг:", reply_markup=await customer_inline_keyboard())
        elif query.data.startswith("cust_"):
            context.user_data["sell_customer"] = query.data.replace("cust_", "")
            await query.message.reply_text("Тўлов турини танланг:", reply_markup=payment_keyboard())
            
    elif action == "pay_debt":
        if query.data.startswith("cust_"):
            customer = query.data.replace("cust_", "")
            debt = await get_debt(customer)
            current_debt = debt.amount if debt else 0
            if current_debt <= 0:
                await query.message.reply_text(f"❌ {customer} қарзи йўқ.")
                await start(update, context)
                return
            context.user_data["pay_debt_customer"] = customer
            await query.message.reply_text(f"👤 {customer} қарзи: {format_currency(current_debt)}\nТўлайдиган суммани киритинг:", reply_markup=back_keyboard())

    elif action == "config":
        if query.data.startswith("prod_"):
            product = query.data.replace("prod_", "")
            context.user_data["config_product"] = product
            await query.message.reply_text(f"🛠 {product} учун янги нархни киритинг (сўм):", reply_markup=back_keyboard())