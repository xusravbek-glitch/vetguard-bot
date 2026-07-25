from datetime import datetime

class Product:
    def __init__(self, id=None, name=None, quantity=0, price=0.0, discount=0.0):
        self.id = id
        self.name = name
        self.quantity = quantity
        self.price = price
        self.discount = discount  # Стандарт чегирма фоизи

class Customer:
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

class Debt:
    def __init__(self, id=None, customer_name=None, amount=0.0):
        self.id = id
        self.customer_name = customer_name
        self.amount = amount

class SaleLog:
    def __init__(self, id=None, timestamp=None, customer=None, product=None, quantity=0, original_price=0.0, discount_applied=0.0, total=0.0, payment_type=None):
        self.id = id
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.customer = customer
        self.product = product
        self.quantity = quantity
        self.original_price = original_price
        self.discount_applied = discount_applied  # Берилган чегирма (суммада)
        self.total = total
        self.payment_type = payment_type
