"""
Connect to Polymarket User WebSocket.

Tracks your order placements, fills, and cancellations in real-time.
Requires authentication (API key + secret + passphrase).

Usage:
    export POLY_API_KEY="YOUR_API_KEY"
    export POLY_API_SECRET="YOUR_API_SECRET"
    export POLY_PASSPHRASE="YOUR_PASSPHRASE"
    python connect_user_ws.py
"""

import asyncio
import json
import os
import websockets

# === Configuration ===
WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/user"

# Load credentials from environment
API_KEY = os.environ.get("POLY_API_KEY", "YOUR_API_KEY")
API_SECRET = os.environ.get("POLY_API_SECRET", "YOUR_API_SECRET")
PASSPHRASE = os.environ.get("POLY_PASSPHRASE", "YOUR_PASSPHRASE")

# Replace with your market's condition_id
CONDITION_ID = "YOUR_CONDITION_ID"


class FillTracker:
    """Track order fills from the User WebSocket."""

    def __init__(self):
        self.fills = {}       # order_id -> fill info
        self.live_orders = {} # order_id -> order info

    def on_event(self, msg: dict):
        event_type = msg.get("event_type", "")

        if event_type == "order":
            status = msg.get("status", "")
            order_id = msg.get("order_id", "")

            if status == "LIVE":
                self.live_orders[order_id] = msg
                print(f"📋 Order LIVE: {order_id[:16]}... "
                      f"side={msg.get('side')} price={msg.get('price')}")

            elif status == "CANCELLED":
                self.live_orders.pop(order_id, None)
                print(f"❌ Order CANCELLED: {order_id[:16]}...")

        elif event_type == "trade":
            order_id = msg.get("order_id", "")
            self.fills[order_id] = {
                "price": msg.get("match_price"),
                "size": msg.get("match_size"),
                "side": msg.get("side"),
                "source": "maker",  # WS fills are maker fills
            }
            self.live_orders.pop(order_id, None)
            print(f"✅ FILL (maker): {order_id[:16]}... "
                  f"price={msg.get('match_price')} size={msg.get('match_size')}")

        else:
            print(f"Unknown event: {event_type} — {json.dumps(msg)[:200]}")


async def main():
    tracker = FillTracker()
    backoff = 1

    while True:
        try:
            # Note: actual auth header construction depends on your setup.
            # The py-clob-client handles this internally.
            # This example shows the conceptual connection.
            async with websockets.connect(
                WS_URL,
                extra_headers={
                    "POLY_API_KEY": API_KEY,
                    "POLY_PASSPHRASE": PASSPHRASE,
                },
                ping_interval=20,
                ping_timeout=10,
            ) as ws:
                backoff = 1
                print(f"Connected to User WebSocket")

                # Subscribe to a market
                subscribe_msg = {
                    "type": "subscribe",
                    "channel": "user",
                    "markets": [CONDITION_ID],
                }
                await ws.send(json.dumps(subscribe_msg))
                print(f"Subscribed to user events for {CONDITION_ID[:16]}...")

                async for raw in ws:
                    msg = json.loads(raw)
                    tracker.on_event(msg)

        except (websockets.ConnectionClosed, ConnectionError, OSError) as e:
            print(f"Disconnected: {e}. Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


if __name__ == "__main__":
    asyncio.run(main())
