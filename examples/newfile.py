import sqlite3
import smtplib

class OrderProcessor:
    def __init__(self):
        self.conn = sqlite3.connect("app.db")
        self.cursor = self.conn.cursor()

    def process(self, user_id, product_id, quantity, payment_type):
        # Step 1: Get user
        self.cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
        user = self.cursor.fetchone()

        if user is None:
            print("User not found")
            return

        # Step 2: Get product
        self.cursor.execute(f"SELECT * FROM products WHERE id = {product_id}")
        product = self.cursor.fetchone()

        if product is None:
            print("Product not found")
            return

        price = product[2]
        total_price = price * quantity

        # Step 3: Payment handling
        if payment_type == "credit":
            print("Processing credit payment...")
            # simulate payment
            if total_price > 10000:
                print("Credit limit exceeded")
                return
        elif payment_type == "paypal":
            print("Redirecting to PayPal...")
        else:
            print("Invalid payment method")
            return

        # Step 4: Save order
        self.cursor.execute(
            f"INSERT INTO orders(user_id, product_id, quantity, total) VALUES ({user_id}, {product_id}, {quantity}, {total_price})"
        )
        self.conn.commit()

        # Step 5: Send email
        server = smtplib.SMTP("smtp.example.com", 587)
        server.starttls()
        server.login("admin@example.com", "password")

        message = f"Hello {user[1]}, your order is confirmed. Total: {total_price}"
        server.sendmail("admin@example.com", user[3], message)
        server.quit()

        print("Order processed successfully")

    def close(self):
        self.conn.close()


# Usage
processor = OrderProcessor()
processor.process(1, 101, 2, "credit")
processor.close()