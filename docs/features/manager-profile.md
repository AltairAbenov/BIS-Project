# Manager profile — week 13

Owner: **Yeleussizova Zhannur**

Log in as `manager@onlineshop.kz` / `Manager123` → **My profile** (`/manager/profile/`).
Couriers and the admin also have a profile (without the shop numbers).

## What it does
- Shows the staff member's name, role, email and the date they joined.
- **Shop summary for the manager:** orders today, orders this month, paid revenue
  this month, unpaid orders now, failed payment attempts, bestseller of the month.
- **My details:** change name and phone (letters-only name, phone saved as +7 XXX XXX XX XX).
  Email and role are changed only by the admin.
- **Change password:** the current password must be correct; the new one has 8+ characters
  with a letter and a digit, is typed twice and must differ from the old one.
  After the change the old password stops working.
- Guests go to the login page; customers get 403 Access denied.

## ERD
`docs/erd/erd_week13.png` — new tables Staff and Deliveries:
Staff 1 : M Deliveries (a courier delivers many orders), Orders 1 : 1 Deliveries.

## Files
`shop/profile/__init__.py`, `shop/profile/profile.py`, `shop/profile/routes.py`,
`shop/templates/profile/profile.html`, `shop/static/css/profile.css`, `docs/erd/erd_week13.png`

## Tests
`python tests/test_manager_profile.py` — 10 cases (P1–P10).
