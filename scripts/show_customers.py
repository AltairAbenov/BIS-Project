"""Print all rows of the Customers table - evidence that registration saves data.
Run from the project folder:  python scripts/show_customers.py
"""
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shop.db")
con = sqlite3.connect(DB)
rows = con.execute(
    "SELECT customer_id, full_name, email, phone, address, "
    "CASE WHEN password_hash IS NULL THEN '-' ELSE 'hashed' END FROM Customers"
).fetchall()
print(f"{'id':<4}{'full_name':<20}{'email':<28}{'phone':<18}{'address':<24}password")
for r in rows:
    print(f"{r[0]:<4}{r[1]:<20}{r[2]:<28}{str(r[3] or '-'):<18}{r[4]:<24}{r[5]}")
con.close()
