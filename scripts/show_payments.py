"""Manager view of payments: every order, who placed it and how many times they tried to pay.
Run from the project folder:  python scripts/show_payments.py
"""
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shop.db")
con = sqlite3.connect(DB)
rows = con.execute("""
    SELECT o.order_id, c.full_name, o.total_amount, o.payment_status,
           COUNT(p.payment_id)                                        AS attempts,
           SUM(CASE WHEN p.status = 'failed' THEN 1 ELSE 0 END)       AS failed,
           COALESCE(GROUP_CONCAT(p.method || ' ' || p.status, ', '), 'no payment yet')
    FROM Orders o
    JOIN Customers c ON c.customer_id = o.customer_id
    LEFT JOIN Payments p ON p.order_id = o.order_id
    GROUP BY o.order_id
    ORDER BY o.order_id
""").fetchall()
print(f"{'order':<7}{'customer':<17}{'total':<9}{'status':<11}{'attempts':<10}{'failed':<8}history")
for r in rows:
    print(f"{r[0]:<7}{r[1]:<17}{int(r[2]):<9}{r[3]:<11}{r[4]:<10}{r[5] or 0:<8}{r[6]}")
con.close()
