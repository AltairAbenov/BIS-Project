# Online Shop

Team project for **Basics of Information Systems** (KBTU, 2026).
A website where a customer registers, finds computer accessories, places an order,
pays or cancels it and leaves a review.

Python 3.10+ · Flask · SQLite

## Run it

```
pip install -r requirements.txt
python run.py
```
Open http://127.0.0.1:5000. Stop with Ctrl+C.
The database `shop.db` is created automatically from the files in `schema/`
(it is not stored in Git — everyone has their own local copy).
To start again with clean test data, stop the app and delete `shop.db`.

## Project structure and owners

| Folder / file | What it is | Owner |
|---|---|---|
| `shop/customer/` | main page, search, product page, ordering, ratings and feedback, registration | Abenov Altair |
| `shop/catalog/` | quantity and warehouse stock, unique products / features / orders | Shointay Aigerim |
| `shop/payments/` | payment page, payment attempts, order cancellation | Khassanov Ramazan |
| `tests/` | automatic tests | each test file names its owner |
| `docs/` | ERD and user-flow diagrams | Yeleussizova Zhannur |
| `shop/__init__.py`, `shop/db.py`, `shop/nav.py`, `shop/templates/base.html`, `shop/static/css/base.css` | shared core | whole team |
| `shop/auth.py` | log in / log out, access rules | whole team |
| `schema/` | database: one SQL file per feature, applied in name order | whole team |

Rules that keep branches from colliding:
- each part of the site is its own folder with its own Blueprint (`bp`) — it is registered automatically;
- each part adds its menu links with `nav.add_link(...)`, nobody edits `base.html` for that;
- a new database feature is a **new** file in `schema/` (`02_...sql`, `03_...sql`), never an edit of an old one;
- each part has its own CSS file in `shop/static/css/` and adds it with `{% block styles %}`;
- each member describes their feature in their own file `docs/features/<feature>.md`
  (how to use it, demo data, tests) — so nobody has to edit this README in a branch.

## How we work with Git

- `main` always works. Nobody pushes to `main` directly.
- Every task is done in its own branch named `name/task`, e.g. `ramazan/payment-tests`.
- When the task works, push the branch and open a **Pull Request** into `main`.
  Another member looks at it, then it is merged.
- Before starting a new task: `git checkout main` and `git pull`, then create the new branch.

## Show the evidence

```
python scripts/show_customers.py   # customers
python scripts/show_orders.py      # orders with products and status, stock left
python scripts/show_payments.py    # manager view: payment attempts per order
python tests/test_payments.py      # payment and cancellation tests
python tests/test_uniqueness.py    # uniqueness and product-feature tests
```

## History

- Week 9 — database design: tables, keys, ERD (Task 9)
- Week 10 — main page and registration; Payments table
- Week 11 — log in, ordering, warehouse checks, payment function
- Week 12 — payment page, cancellation, search / filter / sort, product features, ratings and feedback, uniqueness rules
- Week 13 — project moved to GitHub; each member works in their own branch
