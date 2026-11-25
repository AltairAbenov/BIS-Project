"""Print all orders with their products and the stock left - evidence that ordering works.
Run from the project folder:  python scripts/show_orders.py
"""
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shop.db")
con = sqlite3.connect(DB)
print("ORDERS")
print(f"{'order':<7}{'customer':<10}{'date':<12}{'status':<11}{'total':<9}products")
for r in con.execute("""
    SELECT o.order_id, o.customer_id, o.order_date, o.payment_status, o.total_amount,
           GROUP_CONCAT(p.name || ' x' || oi.quantity || ' @' || CAST(oi.unit_price AS INTEGER), ', ')
    FROM Orders o
    JOIN Order_Items oi ON oi.order_id = o.order_id
    JOIN Products p ON p.product_id = oi.product_id
    GROUP BY o.order_id ORDER BY o.order_id"""):
    print(f"{r[0]:<7}{r[1]:<10}{r[2]:<12}{r[3]:<11}{int(r[4]):<9}{r[5]}")
print("\nSTOCK")
for r in con.execute("SELECT product_id, name, stock_qty FROM Products ORDER BY product_id"):
    print(f"{r[0]:<4}{r[1]:<22}{r[2]}")
con.close()
