"""
Place a GTC order on Polymarket via py-clob-client.

Usage:
    export POLY_PRIVATE_KEY="YOUR_PRIVATE_KEY"
    python place_order.py
"""

import os
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

# === Configuration ===
HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  # Polygon mainnet
PRIVATE_KEY = os.environ.get("POLY_PRIVATE_KEY", "YOUR_PRIVATE_KEY")

# 0 = EOA wallet, 2 = Poly proxy wallet
SIGNATURE_TYPE = 0

# Replace with actual token ID
TOKEN_ID = "YOUR_TOKEN_ID"

# Order parameters
SIDE = "BUY"
PRICE = 0.48     # Limit price
SIZE = 50.0      # Number of shares


def main():
    # Initialize the client
    client = ClobClient(
        host=HOST,
        chain_id=CHAIN_ID,
        key=PRIVATE_KEY,
        signature_type=SIGNATURE_TYPE,
    )

    # Create/derive API credentials (first time creates, subsequent derives)
    creds = client.create_or_derive_api_creds()
    client.set_api_creds(creds)
    print("API credentials set")

    # Create and sign the order
    order_args = OrderArgs(
        price=PRICE,
        size=SIZE,
        side=SIDE,
        token_id=TOKEN_ID,
    )
    signed_order = client.create_order(order_args)
    print(f"Order signed: {SIDE} {SIZE} shares at ${PRICE}")

    # Submit the order
    resp = client.post_order(signed_order, OrderType.GTC)

    order_id = resp.get("orderID", "unknown")
    status = resp.get("status", "unknown")

    print(f"Order ID: {order_id}")
    print(f"Status: {status}")

    if status == "LIVE":
        print("✅ Order is on the book, waiting for a match")
    elif status == "MATCHED":
        print("✅ Order was immediately filled (taker fill)")
        print("   Do NOT add to pending orders — it's already done!")
    else:
        print(f"⚠️ Unexpected status: {status}")


if __name__ == "__main__":
    main()
