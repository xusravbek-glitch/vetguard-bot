from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select, update, delete, text
from sqlalchemy.exc import SQLAlchemyError
import logging

from config import DATABASE_URL
from models import Base, Product, Customer, Debt, SaleLog

logger = logging.getLogger(__name__)

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    poolclass=NullPool,
    pool_pre_ping=True
)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # --- Устун етишмаслиги хатосини олдини олиш учун қўшилди ---
            try:
                await conn.execute(
                    text("ALTER TABLE sale_logs ADD COLUMN IF NOT EXISTS original_price FLOAT DEFAULT 0.0;")
                )
            except Exception as e:
                pass
            # ------------------------------------------------------------
        logger.info("✅ База муваффақиятли ишга тушди ва жадваллар яратилди")
    except SQLAlchemyError as e:
        logger.error(f"❌ Database initialization error: {e}")
        raise

# --- ДОРИЛАР БОШҚАРУВИ ---
async def get_product(name: str):
    try:
        async with async_session() as session:
            result = await session.execute(select(Product).where(Product.name.ilike(name.strip())))
            return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_product error: {e}")
        return None

async def get_all_products():
    try:
        async with async_session() as session:
            result = await session.execute(select(Product).order_by(Product.name))
            return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_all_products error: {e}")
        return []

async def add_product(name: str, quantity: int = 0, price: float = 0.0, discount: float = 0.0):
    try:
        async with async_session() as session:
            existing = await get_product(name)
            if existing:
                return existing
            product = Product(name=name.strip(), quantity=quantity, price=price, discount=discount)
            session.add(product)
            await session.commit()
            return product
    except SQLAlchemyError as e:
        logger.error(f"❌ add_product error: {e}")
        raise

async def update_product_quantity(name: str, new_quantity: int):
    try:
        if new_quantity < 0:
            new_quantity = 0
        async with async_session() as session:
            await session.execute(
                update(Product).where(Product.name.ilike(name.strip())).values(quantity=new_quantity)
            )
            await session.commit()
    except SQLAlchemyError as e:
        logger.error(f"❌ update_product_quantity error: {e}")
        raise

async def update_product_details(name: str, price: float, discount: float):
    try:
        async with async_session() as session:
            await session.execute(
                update(Product).where(Product.name.ilike(name.strip())).values(price=price, discount=discount)
            )
            await session.commit()
    except SQLAlchemyError as e:
        logger.error(f"❌ update_product_details error: {e}")
        raise

# --- МИЖОЗЛАР БОШҚАРУВИ ---
async def get_customer(name: str):
    try:
        async with async_session() as session:
            result = await session.execute(select(Customer).where(Customer.name.ilike(name.strip())))
            return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_customer error: {e}")
        return None

async def get_all_customers():
    try:
        async with async_session() as session:
            result = await session.execute(select(Customer).order_by(Customer.name))
            return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_all_customers error: {e}")
        return []

async def add_customer(name: str):
    try:
        async with async_session() as session:
            existing = await get_customer(name)
            if existing:
                return existing
            customer = Customer(name=name.strip())
            session.add(customer)
            await session.commit()
            return customer
    except SQLAlchemyError as e:
        logger.error(f"❌ add_customer error: {e}")
        raise

# --- ҚАРЗЛАР БОШҚАРУВИ ---
async def get_debt(customer_name: str):
    try:
        async with async_session() as session:
            result = await session.execute(select(Debt).where(Debt.customer_name.ilike(customer_name.strip())))
            return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_debt error: {e}")
        return None

async def get_all_debts():
    try:
        async with async_session() as session:
            result = await session.execute(select(Debt).where(Debt.amount > 0))
            return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_all_debts error: {e}")
        return []

async def update_debt(customer_name: str, new_amount: float):
    try:
        customer_name = customer_name.strip()
        async with async_session() as session:
            if new_amount <= 0:
                await session.execute(delete(Debt).where(Debt.customer_name.ilike(customer_name)))
            else:
                result = await session.execute(select(Debt).where(Debt.customer_name.ilike(customer_name)))
                debt = result.scalar_one_or_none()
                if debt:
                    await session.execute(update(Debt).where(Debt.customer_name.ilike(customer_name)).values(amount=new_amount))
                else:
                    new_debt = Debt(customer_name=customer_name, amount=new_amount)
                    session.add(new_debt)
            await session.commit()
    except SQLAlchemyError as e:
        logger.error(f"❌ update_debt error: {e}")
        raise

# --- СОТУВ ЛОГЛАРИ ---
async def log_sale(customer: str, product: str, quantity: int, original_price: float, discount_applied: float, total: float, payment_type: str):
    try:
        async with async_session() as session:
            from datetime import datetime
            log = SaleLog(
                customer=customer.strip(),
                product=product.strip(),
                quantity=quantity,
                original_price=original_price,
                discount_applied=discount_applied,
                total=total,
                payment_type=payment_type,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(log)
            await session.commit()
    except SQLAlchemyError as e:
        logger.error(f"❌ log_sale error: {e}")
        raise

async def get_sale_logs(limit: int = 50):
    try:
        async with async_session() as session:
            result = await session.execute(select(SaleLog).order_by(SaleLog.id.desc()).limit(limit))
            return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_sale_logs error: {e}")
        return []
