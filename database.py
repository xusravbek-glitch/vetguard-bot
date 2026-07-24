from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select, update, delete, func

from config import DATABASE_URL
from models import Base, Product, Customer, Debt, SaleLog

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    poolclass=NullPool,
    pool_pre_ping=True
)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- PRODUCTS ---
async def get_product(name: str):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.name == name))
        return result.scalar_one_or_none()

async def get_all_products():
    async with async_session() as session:
        result = await session.execute(select(Product).order_by(Product.name))
        return result.scalars().all()

async def update_product_quantity(name: str, new_quantity: int):
    async with async_session() as session:
        await session.execute(
            update(Product).where(Product.name == name).values(quantity=new_quantity)
        )
        await session.commit()

async def update_product_details(name: str, price: float, discount: float):
    async with async_session() as session:
        await session.execute(
            update(Product).where(Product.name == name).values(price=price, discount=discount)
        )
        await session.commit()

async def add_product(name: str):
    async with async_session() as session:
        session.add(Product(name=name, quantity=0, price=0, discount=0))
        await session.commit()

# --- CUSTOMERS ---
async def get_all_customers():
    async with async_session() as session:
        result = await session.execute(select(Customer).order_by(Customer.name))
        return result.scalars().all()

async def add_customer(name: str):
    async with async_session() as session:
        session.add(Customer(name=name))
        await session.commit()

# --- DEBTS ---
async def get_debt(customer_name: str):
    async with async_session() as session:
        result = await session.execute(select(Debt).where(Debt.customer_name == customer_name))
        return result.scalar_one_or_none()

async def get_all_debts():
    async with async_session() as session:
        result = await session.execute(select(Debt).where(Debt.amount > 0))
        return result.scalars().all()

async def update_debt(customer_name: str, new_amount: float):
    async with async_session() as session:
        if new_amount <= 0:
            await session.execute(delete(Debt).where(Debt.customer_name == customer_name))
        else:
            debt = await get_debt(customer_name)
            if debt:
                await session.execute(
                    update(Debt).where(Debt.customer_name == customer_name).values(amount=new_amount)
                )
            else:
                session.add(Debt(customer_name=customer_name, amount=new_amount))
        await session.commit()

# --- SALE LOGS ---
async def log_sale(customer: str, product: str, quantity: int, total: float, payment_type: str):
    async with async_session() as session:
        session.add(
            SaleLog(
                customer=customer,
                product=product,
                quantity=quantity,
                total=total,
                payment_type=payment_type,
            )
        )
        await session.commit()

async def get_sale_logs(limit: int = 100):
    async with async_session() as session:
        result = await session.execute(
            select(SaleLog).order_by(SaleLog.id.desc()).limit(limit)
        )
        return result.scalars().all()
