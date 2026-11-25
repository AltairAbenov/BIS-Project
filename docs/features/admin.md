# Admin — week 13

Owner: **Bakyt Aiganym**

Log in as `admin@onlineshop.kz` / `Admin123` → **Staff accounts** (`/admin/`).

## What it does
- Shows every staff account: name, email, phone, role, active / disabled, date created.
- **Create a manager or courier account** with a temporary password.
  Rules: name with letters only; valid email that is not used by any customer or
  staff member; password 8+ characters with a letter and a digit (stored only as a hash);
  phone saved as +7 XXX XXX XX XX. Admin accounts cannot be created from the website.
- **Disable / Enable** an account. A disabled account cannot log in, and a person who is
  already logged in loses access on the next click. The admin cannot disable themselves.

## Access by role (security)
| Who opens /admin/ | Result |
|---|---|
| guest | sent to the login page |
| customer, manager, courier | 403 Access denied |
| admin | the page opens |

## Files
`shop/admin/__init__.py`, `shop/admin/accounts.py`, `shop/admin/routes.py`,
`shop/templates/admin/staff.html`, `shop/static/css/admin.css`

## Tests
`python tests/test_admin.py` — 11 cases (AD1–AD11).
