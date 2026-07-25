import aiosqlite
import os

DB_PATH = "vetguard.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Дорилар жадвали
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                quantity INTEGER DEFAULT 0,
                price REAL DEFAULT 0,
                discount REAL DEFAULT 0
            )
        """)
        # Мижозлар жадвали
        await db.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)
        # Қарздорлар жадвали
        await db.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT UNIQUE,
                amount REAL DEFAULT 0
            )
        """)
        # Сотувлар тарихи жадвали
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT,
                product TEXT,
                quantity INTEGER,
                price REAL,
                discount_applied REAL,
                total REAL,
                payment_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_product(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name, quantity, price, discount FROM products WHERE name = ?", (name,)) as cursor:
            row = await cursor.fetchone()
            if row:
                from collections import namedtuple
                Product = namedtuple("Product", ["name", "quantity", "price", "discount"])
                return Product(*row)
            return None

async def get_all_products():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name, quantity, price, discount FROM products ORDER BY name") as cursor:
            rows = await cursor.fetchall()
            from collections import namedtuple
            Product = namedtuple("Product", ["name", "quantity", "price", "discount"])
            return [Product(*row) for row in rows]

async def add_product(name: str, quantity: int = 0, price: float = 0, discount: float = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO products (name, quantity, price, discount) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET quantity = quantity + ?
        """, (name, quantity, price, discount, quantity))
        await db.commit()

async def update_product_quantity(name: str, quantity: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE products SET quantity = ? WHERE name = ?", (quantity, name))
        await db.commit()

async def update_product_details(name: str, price: float, discount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE products SET price = ?, discount = ? WHERE name = ?", (price, discount, name))
        await db.commit()

async def add_customer(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO customers (name) VALUES (?)", (name,))
        await db.commit()

async def get_all_customers():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name FROM customers ORDER BY name") as cursor:
            rows = await cursor.fetchall()
            from collections import namedtuple
            Customer = namedtuple("Customer", ["name"])
            return [Customer(*row) for row in rows]

async def get_debt(customer_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT customer_name, amount FROM debts WHERE customer_name = ?", (customer_name,)) as cursor:
            row = await cursor.fetchone()
            if row:
                from collections import namedtuple
                Debt = namedtuple("Debt", ["customer_name", "amount"])
                return Debt(*row)
            return None

async def get_all_debts():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT customer_name, amount FROM debts WHERE amount > 0 ORDER BY amount DESC") as cursor:
            rows = await cursor.fetchall()
            from collections import namedtuple
            Debt = namedtuple("Debt", ["customer_name", "amount"])
            return [Debt(*row) for row in rows]

async def update_debt(customer_name: str, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO debts (customer_name, amount) VALUES (?, ?)
            ON CONFLICT(customer_name) DO UPDATE SET amount = ?
        """, (customer_name, amount, amount))
        await db.commit()

async def log_sale(customer: str, product: str, quantity: int, price: float, discount_applied: float, total: float, payment_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO sales (customer, product, quantity, price, discount_applied, total, payment_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (customer, product, quantity, price, discount_applied, total, payment_type))
        await db.commit()

async def get_sale_logs():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT customer, product, quantity, price, discount_applied, total, payment_type, timestamp FROM sales ORDER BY id DESC") as cursor:
            return await cursor.fetchall()

async def get_sale_logs_by_period(days: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT customer, product, quantity, price, discount_applied, total, payment_type, timestamp 
               FROM sales 
               WHERE timestamp >= datetime('now', ? || ' days', 'localtime')
               ORDER BY id DESC""",
            (f"-{days}",)
        ) as cursor:
            return await cursor.fetchall()

async def get_sale_logs_today():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT customer, product, quantity, price, discount_applied, total, payment_type, timestamp 
               FROM sales 
               WHERE date(timestamp) = date('now', 'localtime')
               ORDER BY id DESC"""
        ) as cursor:
            return await cursor.fetchall()
