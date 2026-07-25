from telegram import Update
from telegram.ext import ContextTypes
from database import *
from keyboards import *
from utils import *
from config import LOW_STOCK_LIMIT
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    await clear_user_data(context)
    await update.message.reply_text(
        "👋 **VETGUARD ERP v3.0 Ассистентига хуш келибсиз!**\n\n"
        "💡 *Бу ерда сиз тугмалардан фойдаланишингиз ёки шунчаки овозли/матнли хабар ва расм юбориб ҳисоб-китоб қилишингиз мумкин.*",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

# --- AI БУЙРУҚЛАРИНИ ИЖРО ЭТИШ (СКИДКА БИЛАН) ---
async def process_ai_action(update: Update, context: ContextTypes.DEFAULT_TYPE, ai_data: dict):
    action = ai_data.get("action")
    
    if action == "sell":
        product_name = ai_data.get("product_name")
        customer_name = ai_data.get("customer_name") or "Умумий харидор"
        quantity = ai_data.get("quantity") or 1
        payment_type = "💳 Насия (Қарзга)" if ai_data.get("payment_type") in ["Насия", "Қарз"] else "💵 Нақд тўлов"

        if not product_name:
            await update.message.reply_text("❌ AI дори номини аниқлай олмади.")
            return

        product = await get_product(product_name)
        if not product:
            await update.message.reply_text(f"❌ Базада **{product_name}** топилмади.", parse_mode="Markdown")
            return

        if product.quantity < quantity:
            await update.message.reply_text(f"❌ Омборда етарли маҳсулот йўқ. Хозирча: {product.quantity} шт.")
            return

        # Скидка / Чегирмани ҳисоблаш
        orig_price = product.price
        subtotal = orig_price * quantity
        
        disc_percent = ai_data.get("discount_percent") or 0
        disc_amount = ai_data.get("discount_amount") or 0
        
        if disc_percent > 0:
            total_discount = subtotal * (disc_percent / 100)
        elif disc_amount > 0:
            total_discount = disc_amount
        else:
            total_discount = subtotal * (product.discount / 100)  # Стандарт скидка

        final_total = max(0, subtotal - total_discount)
        new_qty = product.quantity - quantity

        # Базани янгилаш
        await update_product_quantity(product.name, new_qty)
        await add_customer(customer_name)

        if payment_type == "💳 Насия (Қарзга)":
            debt = await get_debt(customer_name)
            curr_debt = debt.amount if debt else 0
            await update_debt(customer_name, curr_debt + final_total)

        await log_sale(customer_name, product.name, quantity, orig_price, total_discount, final_total, payment_type)

        msg = (
            f"🤖 **AI Сотув амалга оширилди!**\n\n"
            f"📦 Дори: **{product.name}**\n"
            f"👤 Мижоз: **{customer_name}**\n"
            f"🔢 Сон: {quantity} шт\n"
            f"💰 Асл нархи: {format_currency(subtotal)}\n"
            f"🏷 Берилган чегирма: {format_currency(total_discount)}\n"
            f"💵 Якуний сумма: **{format_currency(final_total)}**\n"
            f"💳 Тўлов: {payment_type}\n"
            f"📉 Омбор қолдиғи: {new_qty} шт"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())

    elif action == "incoming":
        p_name = ai_data.get("product_name")
        qty = ai_data.get("quantity") or 0
        if not p_name or qty <= 0:
            await update.message.reply_text("❌ Кирим маълумоти аниқланмади.")
            return

        product = await get_product(p_name)
        if not product:
            await add_product(p_name, quantity=qty)
        else:
            await update_product_quantity(product.name, product.quantity + qty)

        await update.message.reply_text(f"🤖 **AI Кирим сақланди:**\n📦 {p_name}: +{qty} шт қўшилди.", reply_markup=main_menu_keyboard())

    elif action == "pay_debt":
        c_name = ai_data.get("customer_name")
        amt = ai_data.get("amount") or 0
        if not c_name or amt <= 0:
            await update.message.reply_text("❌ Қарз тўлови аниқланмади.")
            return

        debt = await get_debt(c_name)
        curr = debt.amount if debt else 0
        new_amt = max(0, curr - amt)
        await update_debt(c_name, new_amt)

        await update.message.reply_text(
            f"🤖 **AI Қарз тўлови:**\n👤 {c_name}\n💵 Тўланди: {format_currency(amt)}\n💰 Қолдиқ қарз: {format_currency(new_amt)}",
            reply_markup=main_menu_keyboard()
        )

    else:
        await update.message.reply_text("❌ Амал аниқланмади. Текшириб қайтадан ёзинг.")

# --- ТУГМАЛАР ОРҚАЛИ КЕТМА-КЕТЛИК (FSM) ---
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    context.user_data["action"] = "add_product"
    await update.message.reply_text("🆕 Янги дори номини киритинг:", reply_markup=back_keyboard())

async def add_product_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    await add_product(name)
    await update.message.reply_text(f"✅ **{name}** базага қўшилди.", parse_mode="Markdown", reply_markup=main_menu_keyboard())
    context.user_data.clear()

async def incoming_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    context.user_data["action"] = "incoming"
    await update.message.reply_text("Кирим қилинадиган дорини танланг:", reply_markup=await product_inline_keyboard())

async def incoming_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Илтимос, фақат сон киритинг.")
        return
    qty = int(update.message.text)
    p_name = context.user_data.get("incoming_product")
    prod = await get_product(p_name)
    if prod:
        await update_product_quantity(p_name, prod.quantity + qty)
        await update.message.reply_text(f"✅ **{p_name}** омборга +{qty} шт қўшилди.", reply_markup=main_menu_keyboard())
    context.user_data.clear()

async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    context.user_data["action"] = "sell"
    await update.message.reply_text("🛒 Сотиладиган дорини танланг:", reply_markup=await product_inline_keyboard())

async def sell_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Сон киритинг.")
        return
    context.user_data["sell_quantity"] = int(update.message.text)
    await update.message.reply_text("🏷 Бу сотув учун СКИДКА (чегирма) суммага киритинг (агар йўқ бўлса 0 ёзинг):", reply_markup=back_keyboard())

async def sell_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Сон киритинг.")
        return
    context.user_data["sell_discount"] = int(update.message.text)
    await update.message.reply_text("💳 Тўлов турини танланг:", reply_markup=payment_keyboard())

async def sell_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.text
    if payment not in ["💵 Нақд тўлов", "💳 Насия (Қарзга)"]: return

    p_name = context.user_data.get("sell_product")
    c_name = context.user_data.get("sell_customer")
    qty = context.user_data.get("sell_quantity")
    discount = context.user_data.get("sell_discount", 0)

    product = await get_product(p_name)
    subtotal = product.price * qty
    final_total = max(0, subtotal - discount)
    new_qty = product.quantity - qty

    await update_product_quantity(p_name, new_qty)
    
    if payment == "💳 Насия (Қарзга)":
        debt = await get_debt(c_name)
        curr = debt.amount if debt else 0
        await update_debt(c_name, curr + final_total)

    await log_sale(c_name, p_name, qty, product.price, discount, final_total, payment)

    msg = (
        f"✅ **Сотув якунланди!**\n\n"
        f"📦 Дори: {p_name}\n"
        f"👤 Мижоз: {c_name}\n"
        f"🔢 Сон: {qty} шт\n"
        f"🏷 Чегирма: {format_currency(discount)}\n"
        f"💵 Топшириладиган сумма: **{format_currency(final_total)}**\n"
        f"💳 Тўлов: {payment}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    context.user_data.clear()

async def config_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    context.user_data["action"] = "config"
    await update.message.reply_text("Созланадиган дорини танланг:", reply_markup=await product_inline_keyboard())

async def config_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit(): return
    context.user_data["config_price"] = float(update.message.text)
    await update.message.reply_text("Стандарт скидка фоизини киритинг (0-99):", reply_markup=back_keyboard())

async def config_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit(): return
    disc = float(update.message.text)
    p_name = context.user_data.get("config_product")
    price = context.user_data.get("config_price")
    
    await update_product_details(p_name, price, disc)
    await update.message.reply_text(f"✅ **{p_name}** нархи: {format_currency(price)} ({disc}% скидка) қилиб янгиланди.", reply_markup=main_menu_keyboard())
    context.user_data.clear()

async def pay_debt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    context.user_data["action"] = "pay_debt"
    await update.message.reply_text("Қарзни тўлайдиган мижозни танланг:", reply_markup=await customer_inline_keyboard())

async def pay_debt_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit(): return
    amt = float(update.message.text)
    c_name = context.user_data.get("pay_debt_customer")
    debt = await get_debt(c_name)
    curr = debt.amount if debt else 0
    new_amt = max(0, curr - amt)
    await update_debt(c_name, new_amt)
    await update.message.reply_text(f"✅ Тўлов қабул қилинди.\n👤 {c_name} қолган қарзи: {format_currency(new_amt)}", reply_markup=main_menu_keyboard())
    context.user_data.clear()

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    products = await get_all_products()
    if not products:
        await update.message.reply_text("📦 Омбор бўш.")
        return
    text = "📦 **Омбордаги мавжуд дорилар:**\n\n"
    for p in products:
        st = "🔴" if p.quantity <= LOW_STOCK_LIMIT else "🟢"
        text += f"{st} **{p.name}** — {p.quantity} шт | {format_currency(p.price)} (Скидка: {p.discount}%)\n"
    MAX_LENGTH = 4000
if len(text) <= MAX_LENGTH:
    await update.message.reply_text(text, parse_mode="Markdown")
else:
    for i in range(0, len(text), MAX_LENGTH):
        await update.message.reply_text(text[i:i + MAX_LENGTH], parse_mode="Markdown")

async def show_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    debts = await get_all_debts()
    if not debts:
        await update.message.reply_text("🎉 Қарздорликлар йўқ!")
        return
    text = "💰 **Насия ва Қарздорлар рўйхати:**\n\n"
    for d in debts:
        text += f"👤 **{d.customer_name}**: {format_currency(d.amount)}\n"
    MAX_LENGTH = 4000
if len(text) <= MAX_LENGTH:
    await update.message.reply_text(text, parse_mode="Markdown")
else:
    for i in range(0, len(text), MAX_LENGTH):
        await update.message.reply_text(text[i:i + MAX_LENGTH], parse_mode="Markdown")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    logs = await get_sale_logs()
    if not logs:
        await update.message.reply_text("📜 Сотувлар тарихи бўш.")
        return
    text = "📜 **Сўнгги сотувлар тарихи:**\n\n"
    for l in logs:
        text += f"⏱ [{l.timestamp}]\n👤 {l.customer} | 📦 {l.product} x{l.quantity} шт\n🏷 Чегирма: {format_currency(l.discount_applied)} | 💵 Сумма: {format_currency(l.total)} ({l.payment_type})\n---\n"
    if len(text) > 4000: text = text[:4000]
    await update.message.reply_text(text)

async def customers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    await update.message.reply_text("👤 Мижозларни бошқариш бўлими:", reply_markup=customer_menu_keyboard())

async def add_customer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    context.user_data["action"] = "add_customer"
    await update.message.reply_text("👤 Янги мижоз исмини киритинг:", reply_markup=back_keyboard())

async def add_customer_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    await add_customer(name)
    await update.message.reply_text(f"✅ Мижоз қўшилди: **{name}**", parse_mode="Markdown", reply_markup=main_menu_keyboard())
    context.user_data.clear()

async def list_customers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context): return
    customers = await get_all_customers()
    if not customers:
        await update.message.reply_text("👥 Мижозлар базаси бўш.")
        return
    text = "📋 **Рўйхатдаги мижозлар:**\n\n"
    for c in customers:
        text += f"• {c.name}\n"
    MAX_LENGTH = 4000
if len(text) <= MAX_LENGTH:
    await update.message.reply_text(text, parse_mode="Markdown")
else:
    for i in range(0, len(text), MAX_LENGTH):
        await update.message.reply_text(text[i:i + MAX_LENGTH], parse_mode="Markdown")

# Inline тугмаларни ушлаш
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_main":
        await start(update, context)
        return

    act = context.user_data.get("action")
    if act == "incoming" and query.data.startswith("prod_"):
        p = query.data.replace("prod_", "")
        context.user_data["incoming_product"] = p
        await query.message.reply_text(f"📥 **{p}** неча дона келди?", reply_markup=back_keyboard())

    elif act == "sell":
        if query.data.startswith("prod_"):
            context.user_data["sell_product"] = query.data.replace("prod_", "")
            await query.message.reply_text("👤 Мижозни танланг:", reply_markup=await customer_inline_keyboard())
        elif query.data.startswith("cust_"):
            context.user_data["sell_customer"] = query.data.replace("cust_", "")
            await query.message.reply_text("🔢 Нечта сотилмоқда (сонини киритинг)?", reply_markup=back_keyboard())

    elif act == "pay_debt" and query.data.startswith("cust_"):
        c = query.data.replace("cust_", "")
        context.user_data["pay_debt_customer"] = c
        await query.message.reply_text(f"💵 **{c}** қанча сумма тўламоқда?", reply_markup=back_keyboard())

    elif act == "config" and query.data.startswith("prod_"):
        p = query.data.replace("prod_", "")
        context.user_data["config_product"] = p
        await query.message.reply_text(f"🛠 **{p}** янги асосий нархини киритинг:", reply_markup=back_keyboard())
