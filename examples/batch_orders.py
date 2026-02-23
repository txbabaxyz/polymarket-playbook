"""
Batch order placement on Polymarket.

Places up to 100 orders in a single HTTP call (0.3-1.3s total).
Much faster than sequential placement (4-6s for the same orders).

Usage:
    export POLY_PRIVATE_KEY="YOUR_PRIVATE_KEY"
    python batch_orders.py
"""

import os
import time
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

# === Configuration ===
HOST = "https://clob.polymarket.com"
CHAIN_ID = 137
PRIVATE_KEY = os.environ.get("POLY_PRIVATE_KEY", "YOUR_PRIVATE_KEY")
SIGNATURE_TYPE = 0

# Replace with actual token IDs
UP_TOKEN_ID = "YOUR_UP_TOKEN_ID"
DN_TOKEN_ID = "YOUR_DN_TOKEN_ID"

# Ladder configuration: (token_id, price, size)
LADDER = [
    # UP side bids
    (UP_TOKEN_ID, 0.46, 50.0),
    (UP_TOKEN_ID, 0.47, 50.0),
    (UP_TOKEN_ID, 0.48, 50.0),
    # DN side bids
    (DN_TOKEN_ID, 0.49, 50.0),
    (DN_TOKEN_ID, 0.50, 50.0),
    (DN_TOKEN_ID, 0.51, 50.0),
]


def main():
    client = ClobClient(
        host=HOST,
        chain_id=CHAIN_ID,
        key=PRIVATE_KEY,
        signature_type=SIGNATURE_TYPE,
    )
    creds = client.create_or_derive_api_creds()
    client.set_api_creds(creds)

    # Sign all orders
    signed_orders = []
    for token_id, price, size in LADDER:
        args = OrderArgs(
            price=price,
            size=size,
            side="BUY",
            token_id=token_id,
        )
        signed_orders.append(client.create_order(args))

    print(f"Signed {len(signed_orders)} orders")

    # Submit batch
    t0 = time.time()
    resp = client.post_orders(signed_orders, OrderType.GTC)
    elapsed = time.time() - t0

    print(f"Batch submitted in {elapsed:.2f}s")

    # Process results
    order_ids = resp.get("orderIDs", [])
    statuses = resp.get("statuses", [])

    live_count = 0
    matched_count = 0

    for oid, status, (token_id, price, size) in zip(order_ids, statuses, LADDER):
        side_label = "UP" if token_id == UP_TOKEN_ID else "DN"
        print(f"  {side_label} ${price:.2f} x{size:.0f} → {status} ({oid[:16]}...)")

        if status == "LIVE":
            live_count += 1
        elif status == "MATCHED":
            matched_count += 1

    print(f"\nSummary: {live_count} live, {matched_count} immediately filled")


if __name__ == "__main__":
    main()
