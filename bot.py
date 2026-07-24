import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Float, select, update, delete

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8205652790:AAERJP2EC3rSXKP1NJ2aXfhmMu6eaJLRHhQ")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "1344327136").split(',')))
DATABASE_URL = os.getenv("DATABASE_URL")

LOW_STOCK_LIMIT = 5

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================
# SQLAlchemy ORM
# ==========================
Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    quantity = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class Debt(Base):
    __tablename__ = 'debts'
    id = Column(Integer, primary_key=True)
    customer_name = Column(String, nullable=False)
    amount = Column(Float, default=0.0)

class SaleLog(Base):
    __tablename__ = 'sale_logs'
    id = Column(Integer, primary_key=True)
    timestamp = Column(String, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    customer = Column(String)
    product = Column(String)
    quantity = Column(Integer)
    total = Column(Float)
    payment_type = Column(String)

engine = create_async_engine(DATABASE_URL, echo=True, poolclass=NullPool)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ==========================
# DATABASE FUNCTIONS
# ==========================
async def get_product(name):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.name == name))
        return result.scalar_one_or_none()

async def get_all_products():
    async with async_session() as session:
        result = await session.execute(select(Product).order_by(Product.name))
        return result.scalars().all()

async def get_all_customers():
    async with async_session() as session:
        result = await session.execute(select(Customer).order_by(Customer.name))
        return result.scalars().all()

async def get_debt(customer_name):
    async with async_session() as session:
        result = await session.execute(select(Debt).where(Debt.customer_name == customer_name))
        return result.scalar_one_or_none()

async def get_all_debts():
    async with async_session() as session:
        result = await session.execute(select(Debt).where(Debt.amount > 0))
        return result.scalars().all()

async def log_sale(customer, product, quantity, total, payment_type):
    async with async_session() as session:
        sale = SaleLog(
            customer=customer,
            product=product,
            quantity=quantity,
            total=total,
            payment_type=payment_type
        )
        session.add(sale)
        await session.commit()

async def get_sale_logs():
    async with async_session() as session:
        result = await session.execute(select(SaleLog).order_by(SaleLog.id.desc()).limit(100))
        return result.scalars().all()

# ==========================
# UTILITIES
# ==========================
def format_currency(amount):
    return f"{amount:,.0f} сўм"

async def get_inventory_text():
    products = await get_all_products()
    if not products:
        return "📦 Омбор бўш."
    lines = ["📦 **Омбор ҳолати:**\n"]
    for p in products:
        status = "🔴" if p.quantity <= LOW_STOCK_LIMIT else "🟢"
        lines.append(f"{status} **{p.name}**")
        lines.append(f"   📦 {p.quantity} дона")
        lines.append(f"   💰 {format_currency(p.price)}")
        lines.append(f"   🎁 {p.discount}% чегирма\n")
    return "\n".join(lines)

async def get_product_keyboard():
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(p.name, callback_data=f"prod_{p.name}")] for p in await get_all_products()
    ] + [[InlineKeyboardButton("⬅️ Орқага", callback_data="back_main")]])
    return markup

async def get_customer_keyboard():
    customers = await get_all_customers()
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(c.name, callback_data=f"cust_{c.name}")] for c in customers
    ] + [[InlineKeyboardButton("⬅️ Орқага", callback_data="back_main")]])
    return markup

# ==========================
# KEYBOARD MENU
# ==========================
def main_menu_keyboard():
    markup = ReplyKeyboardMarkup([
        [KeyboardButton("➕ Келди"), KeyboardButton("➖ Сотиш")],
        [KeyboardButton("📦 Омбор қолдиғи"), KeyboardButton("💰 Қарздорлик")],
        [KeyboardButton("💸 Қарзни тўлаш"), KeyboardButton("⚙️ Дори созлаш")],
        [KeyboardButton("👤 Мижозлар"), KeyboardButton("🆕 Янги дори қўшиш")],
        [KeyboardButton("📜 Умумий тарих")]
    ], resize_keyboard=True)
    return markup

# ==========================
# START
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Рухсат йўқ.")
        return
    await update.message.reply_text("📦 **VETGUARD ERP v3.0 (PostgreSQL)**", reply_markup=main_menu_keyboard(), parse_mode="Markdown")

# ==========================
# 1. ЯНГИ ДОРИ ҚЎШИШ
# ==========================
async def add_new_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🆕 Янги дори номини киритинг:", reply_markup=None)
    context.user_data['action'] = 'add_product'

async def add_new_product_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❌ Ном бўш бўлмасин.")
        return
    existing = await get_product(name)
    if existing:
        await update.message.reply_text(f"❌ {name} аллақачон бор.")
        await start(update, context)
        return
    async with async_session() as session:
        session.add(Product(name=name, quantity=0, price=0, discount=0))
        await session.commit()
    logger.info(f"Янги дори қўшилди: {name}")
    await update.message.reply_text(f"✅ {name} қўшилди.", reply_markup=main_menu_keyboard())
    await start(update, context)

# ==========================
# 2. ДОРИ КЕЛИШИ
# ==========================
async def incoming_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Дорини танланг:", reply_markup=await get_product_keyboard())

async def incoming_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product = query.data.replace("prod_", "")
    context.user_data['incoming_product'] = product
    await query.message.reply_text(f"📥 {product} миқдорини киритинг:", reply_markup=None)
    context.user_data['action'] = 'incoming_quantity'

async def incoming_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Сон киритинг.")
        return
    quantity = int(update.message.text)
    product_name = context.user_data.get('incoming_product')
    product = await get_product(product_name)
    if not product:
        await update.message.reply_text("❌ Дори топилмади.")
        return
    async with async_session() as session:
        await session.execute(update(Product).where(Product.name == product_name).values(quantity=Product.quantity + quantity))
        await session.commit()
    logger.info(f"Келди: {product_name} +{quantity}")
    await update.message.reply_text(f"✅ {product_name} миқдори {quantity} донага ошди.", reply_markup=main_menu_keyboard())
    await start(update, context)

# ==========================
# 3. СОТИШ
# ==========================
async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Дорини танланг:", reply_markup=await get_product_keyboard())

async def sell_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product = query.data.replace("prod_", "")
    context.user_data['sell_product'] = product
    await query.message.reply_text("👤 Мижозни танланг:", reply_markup=await get_customer_keyboard())
    context.user_data['action'] = 'sell_customer'

async def sell_customer_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        customer = query.data.replace("cust_", "")
    else:
        customer = update.message.text.strip()
    customers = await get_all_customers()
    if not any(c.name == customer for c in customers):
        await update.message.reply_text("❌ Мижоз топилмади.")
        return
    context.user_data['sell_customer'] = customer
    markup = ReplyKeyboardMarkup([["💵 Нақд", "💳 Насия"]], resize_keyboard=True)
    await update.message.reply_text("Тўлов турини танланг:", reply_markup=markup)
    context.user_data['action'] = 'sell_payment'

async def sell_payment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.text
    if payment not in ["💵 Нақд", "💳 Насия"]:
        await update.message.reply_text("❌ Нотўғри танлов.")
        return
    context.user_data['sell_payment'] = payment
    product_name = context.user_data.get('sell_product')
    product = await get_product(product_name)
    if not product:
        await update.message.reply_text("❌ Дори топилмади.")
        return
    final_price = product.price * (1 - product.discount / 100)
    await update.message.reply_text(
        f"💵 {product_name} нархи: {format_currency(final_price)} (чегирма {product.discount}%)\n"
        f"Миқдорини киритинг:",
        reply_markup=None
    )
    context.user_data['sell_final_price'] = final_price
    context.user_data['action'] = 'sell_quantity'

async def sell_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Сон киритинг.")
        return
    quantity = int(update.message.text)
    if quantity <= 0:
        await update.message.reply_text("❌ Миқдор 0 дан катта бўлиши керак.")
        return
    product_name = context.user_data.get('sell_product')
    customer = context.user_data.get('sell_customer')
    payment_type = context.user_data.get('sell_payment')
    final_price = context.user_data.get('sell_final_price')
    product = await get_product(product_name)
    if not product or product.quantity < quantity:
        available = product.quantity if product else 0
        await update.message.reply_text(f"❌ Омборда {available} дона бор.")
        return
    total = int(final_price * quantity)
    async with async_session() as session:
        await session.execute(update(Product).where(Product.name == product_name).values(quantity=Product.quantity - quantity))
        if payment_type == "💳 Насия":
            debt = await get_debt(customer)
            if debt:
                await session.execute(update(Debt).where(Debt.customer_name == customer).values(amount=Debt.amount + total))
            else:
                session.add(Debt(customer_name=customer, amount=total))
        await log_sale(customer, product_name, quantity, total, payment_type)
        await session.commit()
    await update.message.reply_text(
        f"✅ Сотилди: {product_name} x{quantity}\n💰 {format_currency(total)}\n📦 Қолди: {product.quantity - quantity}",
        reply_markup=main_menu_keyboard()
    )
    if product.quantity - quantity <= LOW_STOCK_LIMIT:
        await update.message.reply_text(f"⚠️ **{product_name}** тугаяпти! {product.quantity - quantity} дона қолди.", parse_mode="Markdown")
    await start(update, context)

# ==========================
# 4. ОМБОР ҚОЛДИҒИ
# ==========================
async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(await get_inventory_text(), parse_mode="Markdown")

# ==========================
# 5. ҚАРЗДОРЛИК
# ==========================
async def show_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    debts = await get_all_debts()
    if not debts:
        await update.message.reply_text("Қарз йўқ.")
        return
    lines = ["💰 **Қарздорлик:**\n"]
    for d in debts:
        if d.amount > 0:
            lines.append(f"👤 {d.customer_name}: {format_currency(d.amount)}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ==========================
# 6. ҚАРЗНИ ТЎЛАШ
# ==========================
async def pay_debt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Мижозни танланг:", reply_markup=await get_customer_keyboard())
    context.user_data['action'] = 'pay_debt_customer'

async def pay_debt_customer_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    customer = query.data.replace("cust_", "")
    debt = await get_debt(customer)
    current_debt = debt.amount if debt else 0
    if current_debt <= 0:
        await query.message.reply_text(f"❌ {customer} қарзи йўқ.")
        return
    context.user_data['pay_debt_customer'] = customer
    await query.message.reply_text(f"👤 {customer} қарзи: {format_currency(current_debt)}\nТўлайдиган суммани киритинг:", reply_markup=None)
    context.user_data['action'] = 'pay_debt_amount'

async def pay_debt_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Сумма киритинг.")
        return
    amount = int(update.message.text)
    if amount <= 0:
        await update.message.reply_text("❌ Сумма нотўғри.")
        return
    customer = context.user_data.get('pay_debt_customer')
    debt = await get_debt(customer)
    current_debt = debt.amount if debt else 0
    if amount > current_debt:
        await update.message.reply_text(f"❌ Қарздан ортиқ тўлайсиз. Қарз: {format_currency(current_debt)}")
        return
    async with async_session() as session:
        new_amount = current_debt - amount
        if new_amount == 0:
            await session.execute(delete(Debt).where(Debt.customer_name == customer))
        else:
            await session.execute(update(Debt).where(Debt.customer_name == customer).values(amount=new_amount))
        await session.commit()
    logger.info(f"ТЎЛОВ: {customer} {amount} сўм тўлади. Қолган қарз: {new_amount}")
    await update.message.reply_text(f"✅ Тўланди. Қолган қарз: {format_currency(new_amount)}", reply_markup=main_menu_keyboard())
    await start(update, context)

# ==========================
# 7. ДОРИ СОЗЛАШ
# ==========================
async def config_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Дорини танланг:", reply_markup=await get_product_keyboard())
    context.user_data['action'] = 'config_product'

async def config_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product = query.data.replace("prod_", "")
    context.user_data['config_product'] = product
    await query.message.reply_text(f"🛠 {product} учун янги нархни киритинг (сўм):", reply_markup=None)
    context.user_data['action'] = 'config_price'

async def config_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Нархни сон киритинг.")
        return
    price = int(update.message.text)
    context.user_data['config_price'] = price
    await update.message.reply_text("Чегирма фоизини киритинг (0-99):", reply_markup=None)
    context.user_data['action'] = 'config_discount'

async def config_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Фоизни сон киритинг.")
        return
    discount = int(update.message.text)
    if discount < 0 or discount > 99:
        await update.message.reply_text("❌ Фоиз 0-99 оралиғида бўлиши керак.")
        return
    product_name = context.user_data.get('config_product')
    price = context.user_data.get('config_price')
    async with async_session() as session:
        await session.execute(update(Product).where(Product.name == product_name).values(price=price, discount=discount))
        await session.commit()
    logger.info(f"Созланди: {product_name} нарх={price}, чегирма={discount}%")
    await update.message.reply_text(
        f"✅ {product_name} янгиланди:\n💰 {format_currency(price)}\n🎁 {discount}% чегирма",
        reply_markup=main_menu_keyboard()
    )
    await start(update, context)

# ==========================
# 8. МИЖОЗЛАР
# ==========================
async def customers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markup = ReplyKeyboardMarkup([["👤 Янги мижоз қўшиш", "⬅️ Орқага"]], resize_keyboard=True)
    await update.message.reply_text("Мижозларни бошқариш:", reply_markup=markup)

async def add_customer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Янги мижоз исми:", reply_markup=None)
    context.user_data['action'] = 'add_customer'

async def add_customer_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❌ Исм бўш бўлмасин.")
        return
    customers = await get_all_customers()
    if any(c.name == name for c in customers):
        await update.message.reply_text(f"❌ {name} аллақачон бор.")
        await start(update, context)
        return
    async with async_session() as session:
        session.add(Customer(name=name))
        await session.commit()
    logger.info(f"Янги мижоз қўшилди: {name}")
    await update.message.reply_text(f"✅ {name} мижозлар рўйхатига қўшилди.", reply_markup=main_menu_keyboard())
    await start(update, context)

# ==========================
# 9. УМУМИЙ ТАРИХ
# ==========================
async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ==========================
# БЕКОР / ОРҚАГА
# ==========================
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_main":
        await start(update, context)

# ==========================
# MAIN
# ==========================
async def post_init(application: Application):
    await init_db()
    logger.info("🚀 VETGUARD ERP v3.0 (Full) ишга тушди!")

def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🆕 Янги дори қўшиш$"), add_new_product_start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^➕ Келди$"), incoming_start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^➖ Сотиш$"), sell_start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📦 Омбор қолдиғи$"), inventory))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💰 Қарздорлик$"), show_debts))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💸 Қарзни тўлаш$"), pay_debt_start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^⚙️ Дори созлаш$"), config_product_start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^👤 Мижозлар$"), customers_menu))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^👤 Янги мижоз қўшиш$"), add_customer_start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📜 Умумий тарих$"), show_logs))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^⬅️ Орқага$"), back_to_main))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(handle_callback, pattern="^back_main$"))
    application.add_handler(CallbackQueryHandler(incoming_product_selected, pattern="^prod_"))
    application.add_handler(CallbackQueryHandler(sell_product_selected, pattern="^prod_"))
    application.add_handler(CallbackQueryHandler(sell_customer_selected, pattern="^cust_"))
    application.add_handler(CallbackQueryHandler(pay_debt_customer_selected, pattern="^cust_"))
    application.add_handler(CallbackQueryHandler(config_product_selected, pattern="^prod_"))

    # Step handlers (text input)
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^[0-9]+$") & filters.ChatType.PRIVATE, lambda u, c: None))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, lambda u, c: None))

    port = int(os.getenv("PORT", 8443))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="/webhook",
        webhook_url=os.getenv("WEBHOOK_URL")
    )

if __name__ == "__main__":
    main()
