from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Product(Base):
    """Дори модели"""
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    quantity = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)

class Customer(Base):
    """Мижоз модели"""
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class Debt(Base):
    """Қарз модели"""
    __tablename__ = "debts"
    id = Column(Integer, primary_key=True)
    customer_name = Column(String, nullable=False, unique=True)
    amount = Column(Float, default=0.0)

class SaleLog(Base):
    """Сотиш логи модели"""
    __tablename__ = "sale_logs"
    id = Column(Integer, primary_key=True)
    timestamp = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    customer = Column(String, nullable=False)
    product = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)
    payment_type = Column(String, nullable=False)
