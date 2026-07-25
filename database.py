from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select, update, delete, func
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
    """Базаны инициализация қилиш"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База инициализирован")
    except SQLAlchemyError as e:
        logger.error(f"❌ База инициализация хатолиги: {e}")
        raise

# --- PRODUCTS ---
async def get_product(name: str):
    """Дорини номи бўйича ола"""
    try:
        async with async_session() as session:
            result = await session.execute(select(Product).where(Product.name == name))
            return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_product xatosi: {e}")
        return None

async def get_all_products():
    """Барча дорилар рўйхатини ола"""
    try:
        async with async_session() as session:
            result = await session.execute(select(Product).order_by(Product.name))
            return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_all_products xatosi: {e}")
        return []

async def add_product(name: str):
    """Янги дори қўшиш"""
    try:
        async with async_session() as session:
            product = Product(name=name, quantity=0, price=0.0, discount=0.0)
            session.add(product)
            await session.commit()
        logger.info(f"✅ Дори қўшилди: {name}")
    except SQLAlchemyError as e:
        logger.error(f"❌ add_product xatosi: {e}")
        raise

async def update_product_quantity(name: str, new_quantity: int):
    """Дори миқдорини янгилаш"""
    try:
        if new_quantity < 0:
            logger.warning(f"⚠️ Сўрамох миқдор: {name} - {new_quantity}")
            new_quantity = 0
        
        async with async_session() as session:
            await session.execute(
                update(Product).where(Product.name == name).values(quantity=new_quantity)
            )
            await session.commit()
        logger.info(f"✅ {name} миқдори янгиланди: {new_quantity}")
    except SQLAlchemyError as e:
        logger.error(f"❌ update_product_quantity xatosi: {e}")
        raise

async def update_product_details(name: str, price: float, discount: float):
    """Дори нарх ва чегирмасини янгилаш"""
    try:
        if price < 0:
            price = 0
        if discount < 0 or discount > 99:
            discount = 0
            
        async with async_session() as session:
            await session.execute(
                update(Product).where(Product.name == name).values(price=price, discount=discount)
            )
            await session.commit()
        logger.info(f"✅ {name} детали янгиланди: {price}, {discount}%")
    except SQLAlchemyError as e:
        logger.error(f"❌ update_product_details xatosi: {e}")
        raise

# --- CUSTOMERS ---
async def get_all_customers():
    """Барча мижозларни ола"""
    try:
        async with async_session() as session:
            result = await session.execute(select(Customer).order_by(Customer.name))
            return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_all_customers xatosi: {e}")
        return []

async def add_customer(name: str):
    """Янги мижоз қўшиш"""
    try:
        async with async_session() as session:
            customer = Customer(name=name)
            session.add(customer)
            await session.commit()
        logger.info(f"✅ Мижоз қўшилди: {name}")
    except SQLAlchemyError as e:
        logger.error(f"❌ add_customer xatosi: {e}")
        raise

# --- DEBTS ---
async def get_debt(customer_name: str):
    """Мижознинг қарзини ола"""
    try:
        async with async_session() as session:
            result = await session.execute(select(Debt).where(Debt.customer_name == customer_name))
            return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_debt xatosi: {e}")
        return None

async def get_all_debts():
    """Барча қарзларни ола"""
    try:
        async with async_session() as session:
            result = await session.execute(select(Debt).where(Debt.amount > 0))
            return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_all_debts xatosi: {e}")
        return []

async def update_debt(customer_name: str, new_amount: float):
    """Мижоз қарзини янгилаш"""
    try:
        if new_amount < 0:
            new_amount = 0
            
        async with async_session() as session:
            if new_amount <= 0:
                # Қарз йўқ болса, қаторни ўчириш
                await session.execute(delete(Debt).where(Debt.customer_name == customer_name))
            else:
                # Сессия ичида қарзни қидириш
                result = await session.execute(
                    select(Debt).where(Debt.customer_name == customer_name)
                )
                debt = result.scalar_one_or_none()
                
                if debt:
                    # Мавжудни янгилаш
                    await session.execute(
                        update(Debt).where(Debt.customer_name == customer_name).values(amount=new_amount)
                    )
                else:
                    # Янгисини қўшиш
                    new_debt = Debt(customer_name=customer_name, amount=new_amount)
                    session.add(new_debt)
            
            await session.commit()
        logger.info(f"✅ {customer_name} қарзи янгиланди: {new_amount}")
    except SQLAlchemyError as e:
        logger.error(f"❌ update_debt xatosi: {e}")
        raise

# --- SALE LOGS ---
async def log_sale(customer: str, product: str, quantity: int, total: float, payment_type: str):
    """Сотиш логини ёзиш"""
    try:
        async with async_session() as session:
            from datetime import datetime
            log = SaleLog(
                customer=customer,
                product=product,
                quantity=quantity,
                total=total,
                payment_type=payment_type,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(log)
            await session.commit()
        logger.info(f"✅ Сотиш логи қўшилди: {customer} → {product}")
    except SQLAlchemyError as e:
        logger.error(f"❌ log_sale xatosi: {e}")
        raise

async def get_sale_logs(limit: int = 100):
    """Сотиш логларини ола"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(SaleLog).order_by(SaleLog.id.desc()).limit(limit)
            )
            return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"❌ get_sale_logs xatosi: {e}")
        return []