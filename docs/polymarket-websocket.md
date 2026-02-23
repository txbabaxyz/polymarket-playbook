# Polymarket WebSocket Channels

> Real-time market data and order updates via WebSocket.

## Table of Contents

- [Overview](#overview)
- [Market Channel](#market-channel)
  - [Connection](#connection)
  - [Subscription](#subscription)
  - [Book Event](#book-event)
  - [Price Change Event](#price-change-event)
  - [Parsing & Tracking](#parsing--tracking)
- [User Channel](#user-channel)
  - [Connection](#user-connection)
  - [Subscription](#user-subscription)
  - [Events](#user-events)
- [Reconnection Strategy](#reconnection-strategy)
- [Code Examples](#code-examples)

---

## Overview

Polymarket provides two WebSocket channels:

| Channel | URL | Purpose |
|---------|-----|---------|
| **Market** | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | Order book snapshots, price changes |
| **User** | `wss://ws-subscriptions-clob.polymarket.com/ws/user` | Your order fills, placements, cancellations |

---

## Market Channel

### Connection

```
wss://ws-subscriptions-clob.polymarket.com/ws/market
```

No authentication required — market data is public.

### Subscription

After connecting, send a subscription message:

```json
{
  "type": "market",
  "assets_id": ["TOKEN_ID_UP", "TOKEN_ID_DN"]
}
```

You can subscribe to multiple token IDs. Each token ID represents one side of a binary market.

### Book Event

Full order book snapshot. Sent on subscription and periodically.

```json
{
  "event_type": "book",
  "asset_id": "TOKEN_ID_UP",
  "market": "CONDITION_ID",
  "bids": [
    {"price": "0.52", "size": "100.0"},
    {"price": "0.51", "size": "250.0"}
  ],
  "asks": [
    {"price": "0.53", "size": "150.0"},
    {"price": "0.54", "size": "200.0"}
  ],
  "timestamp": "1700000000",
  "hash": "0x..."
}
```

### Price Change Event

Lightweight update when best bid/ask changes.

```json
{
  "event_type": "price_change",
  "asset_id": "TOKEN_ID_UP",
  "price": "0.525",
  "side": "buy",
  "size": "75.0",
  "timestamp": "1700000001"
}
```

### Parsing & Tracking

To track the current state of a market:

```python
class BookTracker:
    def __init__(self):
        self.best_bid = {}  # token_id -> price
        self.best_ask = {}  # token_id -> price

    def handle_book(self, msg):
        """Process full book snapshot."""
        asset_id = msg["asset_id"]
        if msg["bids"]:
            self.best_bid[asset_id] = float(msg["bids"][0]["price"])
        if msg["asks"]:
            self.best_ask[asset_id] = float(msg["asks"][0]["price"])

    def handle_price_change(self, msg):
        """Process price change event."""
        asset_id = msg["asset_id"]
        price = float(msg["price"])
        if msg["side"] == "buy":
            self.best_bid[asset_id] = price
        else:
            self.best_ask[asset_id] = price

    def sigma(self, up_token_id, dn_token_id):
        """Calculate sigma = up_ask + dn_ask.
        σ = 1.00 is perfect (zero spread).
        σ > 1.05 means wide spread — market making is expensive.
        """
        up_ask = self.best_ask.get(up_token_id, float("inf"))
        dn_ask = self.best_ask.get(dn_token_id, float("inf"))
        return up_ask + dn_ask
```

---

## User Channel

### User Connection

```
wss://ws-subscriptions-clob.polymarket.com/ws/user
```

Requires authentication headers (same as REST API L2 auth).

### User Subscription

```json
{
  "type": "subscribe",
  "channel": "user",
  "markets": ["CONDITION_ID_1", "CONDITION_ID_2"]
}
```

### User Events

#### Order Placement Confirmation

```json
{
  "event_type": "order",
  "order_id": "0xORDER_ID",
  "status": "LIVE",
  "side": "BUY",
  "price": "0.50",
  "size": "100.0",
  "asset_id": "TOKEN_ID",
  "timestamp": "1700000000"
}
```

#### Order Fill (Maker)

```json
{
  "event_type": "trade",
  "order_id": "0xORDER_ID",
  "status": "MATCHED",
  "match_price": "0.50",
  "match_size": "50.0",
  "asset_id": "TOKEN_ID",
  "side": "BUY",
  "timestamp": "1700000002"
}
```

**Critical**: This is how you detect **maker fills**. Taker fills come from the POST /order response. You MUST track both sources to have accurate fill data.

#### Order Cancellation

```json
{
  "event_type": "order",
  "order_id": "0xORDER_ID",
  "status": "CANCELLED",
  "timestamp": "1700000003"
}
```

---

## Reconnection Strategy

WebSocket connections **will** drop. Plan for it.

```python
import asyncio
import websockets
import json

async def connect_with_reconnect(url, subscribe_msg, handler):
    """Robust WebSocket connection with automatic reconnection."""
    backoff = 1
    max_backoff = 60

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                backoff = 1  # Reset on successful connect
                await ws.send(json.dumps(subscribe_msg))

                async for raw in ws:
                    msg = json.loads(raw)
                    await handler(msg)

        except (websockets.ConnectionClosed, ConnectionError, OSError) as e:
            print(f"WS disconnected: {e}. Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
```

### Key Points

- Set `ping_interval=20` and `ping_timeout=10` for keepalive
- Use exponential backoff on reconnection (cap at 60s)
- Re-subscribe after reconnection — subscriptions are not persisted
- Preserve local state (book tracker, order tracker) across reconnections
- Request a fresh book snapshot after reconnecting to avoid stale state

---

## Code Examples

See full working examples:
- [connect_clob_ws.py](../examples/connect_clob_ws.py) — Market channel
- [connect_user_ws.py](../examples/connect_user_ws.py) — User channel

---

*See also: [CLOB API](polymarket-api.md) · [Order Management](polymarket-orders.md) · [Metrics](metrics-calculations.md)*
