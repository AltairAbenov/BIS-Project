# Search, sorting and the courier page — week 13

Owner: **Abenov Altair**

## Search and sorting (main page)
- Every word of the search is looked for in the product name, the category
  **and the product features**: "bluetooth" finds the Wireless Mouse,
  "usb-c 1tb" finds the External SSD. A card shows where the word was found.
- Price range "from – to" (in tenge); if "from" is bigger than "to", they are swapped.
- "In stock only" hides products with stock 0.
- Sorting: best rated, **bestsellers** (units sold in paid orders), price low → high,
  price high → low, name.
- Code: `shop/customer/search.py` (all values go into SQL as parameters).

## Courier page `/courier/`
Log in as `courier@onlineshop.kz` / `Courier123`.
- **Waiting for a courier** — only PAID orders that nobody has taken yet,
  with the customer's address, phone and products (no email, no payment details).
- **Take this order** → the order is "on the way" with this courier.
- **Mark as delivered** → only the courier who took the order can do it; the time is saved.
- New table `Deliveries` (`schema/03_deliveries.sql`): Orders 1 : 1 Deliveries,
  `order_id` is UNIQUE, so two couriers can never take the same order.
- The customer sees the delivery status on the order page:
  waiting for a courier → on the way → delivered.

## Files
`shop/customer/search.py`, `shop/customer/routes.py` (main page, order page),
`shop/templates/customer/index.html`, `shop/templates/customer/order_detail.html`,
`shop/static/css/customer.css`, `schema/03_deliveries.sql`, `shop/courier/`,
`shop/templates/courier/deliveries.html`, `shop/static/css/courier.css`

## Tests
`python tests/test_search_courier.py` — 15 cases (S1–S7 search, K1–K8 courier).
