# Whole payment process — tests, week 13

Owner: **Khassanov Ramazan**

`tests/test_payments.py` checks the payment functions one by one (R1–R6, C1–C5).
`tests/test_payment_process.py` checks **the whole payment process through the website**,
the way a customer clicks it: register → order → payment page → declined → try again →
paid, and the cancel path. Each run uses a fresh temporary database.

Run: `python tests/test_payment_process.py`

| # | Case | What must happen |
|---|---|---|
| W1 | Guest opens or sends the payment page | sent to login, nothing saved |
| W2 | Order 2 × External SSD | order pending, 90 000 ₸, stock reserved (8 → 6) |
| W3 | Payment page | shows “Pay 90 000 ₸” and “Cancel order instead” |
| W4 | Bank declines | status failed, attempt saved, stock still reserved |
| W5 | Try again with `amount=1` in the request | paid 90 000 ₸ — amount comes from the order |
| W6 | Attempt history | card failed → kaspi paid, shown on the order page |
| W7 | Pay a paid order again | “nothing to pay”, no new attempt |
| W8 | Double click on “Pay” | only one successful payment |
| W9 | Unknown payment method | rejected, nothing saved |
| W10 | Declined, then cancel, then pay | cancelled, stock returned, failed attempt kept, payment blocked |
| W11 | Cancel a paid order | rejected, still paid |
| W12 | Another customer uses my order number | 404, nothing changed |
| W13 | Manager opens the order | sees both attempts |

Result on 2026-11-25: **13 of 13 passed.** No defects found in the payment code.
