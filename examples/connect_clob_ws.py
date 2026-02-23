"""
Connect to Polymarket CLOB Market WebSocket.

Subscribes to a market's order book and tracks best bid/ask prices.
No authentication required — market data is public.

Usage:
    python connect_clob_ws.py
"""

import asyncio
import json
import websockets

# === Configuration ===
WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

# Replace with actual token IDs for the market you want to track
UP_TOKEN_ID = "YOUR_UP_TOKEN_ID"
DN_TOKEN_ID = "YOUR_DN_TOKEN_ID"


class BookTracker:
    """Track best bid/ask for UP and DN tokens."""

    def __init__(self):
        self.best_bid = {}  # token_id -> float
        self.best_ask = {}  # token_id -> float

    def handle_book(self, msg: dict):
        """Process full order book snapshot."""
        asset_id = msg["asset_id"]
        if msg.get("bids"):
            self.best_bid[asset_id] = float(msg["bids"][0]["price"])
        if msg.get("asks"):
            self.best_ask[asset_id] = float(msg["asks"][0]["price"])

    def handle_price_change(self, msg: dict):
        """Process price change event."""
        asset_id = msg["asset_id"]
        price = float(msg["price"])
        if msg.get("side") == "buy":
            self.best_bid[asset_id] = price
        else:
            self.best_ask[asset_id] = price

    def sigma(self) -> float:
        """Calculate sigma = up_ask + dn_ask."""
        up_ask = self.best_ask.get(UP_TOKEN_ID, float("inf"))
        dn_ask = self.best_ask.get(DN_TOKEN_ID, float("inf"))
        return up_ask + dn_ask

    def display(self):
        """Print current state."""
        up_bid = self.best_bid.get(UP_TOKEN_ID, "?")
        up_ask = self.best_ask.get(UP_TOKEN_ID, "?")
        dn_bid = self.best_bid.get(DN_TOKEN_ID, "?")
        dn_ask = self.best_ask.get(DN_TOKEN_ID, "?")
        sigma = self.sigma()
        print(f"UP: {up_bid}/{up_ask}  DN: {dn_bid}/{dn_ask}  σ={sigma:.4f}")


async def main():
    tracker = BookTracker()
    backoff = 1

    while True:
        try:
            async with websockets.connect(
                WS_URL, ping_interval=20, ping_timeout=10
            ) as ws:
                backoff = 1  # Reset on successful connect
                print(f"Connected to {WS_URL}")

                # Subscribe to both tokens
                subscribe_msg = {
                    "type": "market",
                    "assets_id": [UP_TOKEN_ID, DN_TOKEN_ID],
                }
                await ws.send(json.dumps(subscribe_msg))
                print("Subscribed to market data")

                async for raw in ws:
                    msg = json.loads(raw)
                    event_type = msg.get("event_type", "")

                    if event_type == "book":
                        tracker.handle_book(msg)
                        tracker.display()
                    elif event_type == "price_change":
                        tracker.handle_price_change(msg)
                        tracker.display()
                    else:
                        print(f"Unknown event: {event_type}")

        except (websockets.ConnectionClosed, ConnectionError, OSError) as e:
            print(f"Disconnected: {e}. Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


if __name__ == "__main__":
    asyncio.run(main())
