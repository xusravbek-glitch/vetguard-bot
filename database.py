import os
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import namedtuple

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

async def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Дорилар жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            quantity INTEGER DEFAULT 0,
            price REAL DEFAULT 0,
            discount REAL DEFAULT 0
        )
    """)
    # Мижозлар жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        )
    """)
    # Қарздорлар жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id SERIAL PRIMARY KEY,
            customer_name TEXT UNIQUE,
            amount REAL DEFAULT 0
        )
    """)
    # Сотувлар тарихи жадвали
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            customer TEXT,
            product TEXT,
            quantity INTEGER,
            price REAL,
            discount_applied REAL,
            total REAL,
            payment_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

async def get_product(name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, quantity, price, discount FROM products WHERE name = %s", (name,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        Product = namedtuple("Product", ["name", "quantity", "price", "discount"])
        return Product(row['name'], row['quantity'], row['price'], row['discount'])
    return None

async def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, quantity, price, discount FROM products ORDER BY name")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    Product = namedtuple("Product", ["name", "quantity", "price", "discount"])
    return [Product(row['name'], row['quantity'], row['price'], row['discount']) for row in rows]

async def add_product(name: str, quantity: int = 0, price: float = 0, discount: float = 0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, quantity, price, discount) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(name) DO UPDATE SET 
            quantity = products.quantity + %s,
            price = %s,
            discount = %s
    """, (name, quantity, price, discount, quantity, price, discount))
    conn.commit()
    cursor.close()
    conn.close()

async def update_product_quantity(name: str, quantity: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET quantity = %s WHERE name = %s", (quantity, name))
    conn.commit()
    cursor.close()
    conn.close()

async def update_product_details(name: str, price: float, discount: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET price = %s, discount = %s WHERE name = %s", (price, discount, name))
    conn.commit()
    cursor.close()
    conn.close()

async def add_customer(name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO customers (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))
    conn.commit()
    cursor.close()
    conn.close()

async def get_all_customers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM customers ORDER BY name")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    Customer = namedtuple("Customer", ["name"])
    return [Customer(row['name']) for row in rows]

async def get_debt(customer_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_name, amount FROM debts WHERE customer_name = %s", (customer_name,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        Debt = namedtuple("Debt", ["customer_name", "amount"])
        return Debt(row['customer_name'], row['amount'])
    return None

async def get_all_debts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_name, amount FROM debts WHERE amount > 0 ORDER BY amount DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    Debt = namedtuple("Debt", ["customer_name", "amount"])
    return [Debt(row['customer_name'], row['amount']) for row in rows]

async def update_debt(customer_name: str, amount: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO debts (customer_name, amount) VALUES (%s, %s)
        ON CONFLICT(customer_name) DO UPDATE SET amount = %s
    """, (customer_name, amount, amount))
    conn.commit()
    cursor.close()
    conn.close()

async def log_sale(customer: str, product: str, quantity: int, price: float, discount_applied: float, total: float, payment_type: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sales (customer, product, quantity, price, discount_applied, total, payment_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (customer, product, quantity, price, discount_applied, total, payment_type))
    conn.commit()
    cursor.close()
    conn.close()

async def get_sale_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer, product, quantity, price, discount_applied, total, payment_type, timestamp FROM sales ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [[r['customer'], r['product'], r['quantity'], r['price'], r['discount_applied'], r['total'], r['payment_type'], r['timestamp']] for r in rows]

async def get_sale_logs_by_period(days: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""SELECT customer, product, quantity, price, discount_applied, total, payment_type, timestamp 
           FROM sales 
           WHERE timestamp >= NOW() - INTERVAL '{days} days'
           ORDER BY id DESC"""
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [[r['customer'], r['product'], r['quantity'], r['price'], r['discount_applied'], r['total'], r['payment_type'], r['timestamp']] for r in rows]

async def get_sale_logs_today():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT customer, product, quantity, price, discount_applied, total, payment_type, timestamp 
           FROM sales 
           WHERE timestamp >= CURRENT_DATE
           ORDER BY id DESC"""
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [[r['customer'], r['product'], r['quantity'], r['price'], r['discount_applied'], r['total'], r['payment_type'], r['timestamp']] for r in rows]
