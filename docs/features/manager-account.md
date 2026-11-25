# Manager account and roles — week 13

Owner: **Shointay Aigerim**

## What it does
- Shop workers have their own accounts in the new table `Staff` (`schema/02_staff.sql`)
  with a role: **manager**, **courier** or **admin**. Customers stay in `Customers`.
- One login page for everybody. After logging in each role opens its own start page.
- `role_required("manager")` protects staff pages: a guest goes to the login page,
  a customer or a courier gets "Access denied" (403).
- A disabled account (`is_active = 0`) cannot log in and loses access at once.
- One email = one account in the whole shop (database triggers stop a customer
  and a staff member with the same email).
- **Manager dashboard** `/manager/`: number of orders, unpaid orders and their sum,
  paid revenue, cancelled orders; all orders with customer, products, status and
  payment attempts; filter by status ("Unpaid only") and search by customer;
  products with low stock (less than 10). Each order opens with its payment attempts.

## Demo accounts (created with the database)

| Role | Email | Password |
|---|---|---|
| manager | manager@onlineshop.kz | Manager123 |
| courier | courier@onlineshop.kz | Courier123 |
| admin | admin@onlineshop.kz | Admin123 |

Passwords are stored only as hashes. Change them before any real use.

## Files
`schema/02_staff.sql`, `shop/auth.py`, `shop/manager/__init__.py`, `shop/manager/routes.py`,
`shop/templates/manager/dashboard.html`, `shop/templates/manager/order.html`,
`shop/templates/auth/403.html`, `shop/static/css/manager.css`

## Tests
`python tests/test_manager_account.py` — 10 cases (M1–M10).
