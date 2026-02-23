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

Polymarket provides four WebSocket channels:

| Channel | URL | Auth | Purpose |
|---------|-----|------|---------|
| **Market** | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | No | Order book snapshots, price changes, market events |
| **User** | `wss://ws-subscriptions-clob.polymarket.com/ws/user` | Yes | Your order fills, placements, cancellations |
| **Sports** | `wss://sports-api.polymarket.com/ws` | No | Live sports scores and game state |
| **RTDS** | `wss://ws-live-data.polymarket.com` | Optional | Real-time comments and crypto prices |

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
  "assets_ids": ["TOKEN_ID_UP", "TOKEN_ID_DN"],
  "type": "market",
  "custom_feature_enabled": true
}
```

**Note**: The field is `assets_ids` (plural), not `assets_id`. Set `custom_feature_enabled: true` to receive `best_bid_ask`, `new_market`, and `market_resolved` events.

### Dynamic Subscription (Without Reconnecting)

```json
{"assets_ids": ["new_id"], "operation": "subscribe", "custom_feature_enabled": true}
{"assets_ids": ["old_id"], "operation": "unsubscribe"}
```

### Message Types

| Type | Trigger | Description |
|------|---------|-------------|
| `book` | On subscribe + on trade | Full orderbook snapshot |
| `price_change` | New order or cancellation | Price level updates |
| `tick_size_change` | Price > 0.96 or < 0.04 | Tick size changed |
| `last_trade_price` | Maker/taker matched | Trade execution with price, size, side |
| `best_bid_ask` | Best prices change | Best bid/ask + spread (requires custom_feature) |
| `new_market` | New market created | Market details + event info (requires custom_feature) |
| `market_resolved` | Market resolved | Winning asset/outcome (requires custom_feature) |

### Book Event

Full order book snapshot. Sent on subscription and after trades.

```json
{
  "event_type": "book",
  "asset_id": "TOKEN_ID_UP",
  "market": "CONDITION_ID",
  "bids": [
    {"price": ".48", "size": "30"},
    {"price": ".49", "size": "20"}
  ],
  "asks": [
    {"price": ".52", "size": "25"},
    {"price": ".53", "size": "60"}
  ],
  "timestamp": "123456789000",
  "hash": "0x..."
}
```

### Price Change Event

Emitted when a new order is placed or cancelled. A `size` of `"0"` means the price level was removed.

```json
{
  "event_type": "price_change",
  "market": "0x...",
  "price_changes": [
    {
      "asset_id": "TOKEN_ID",
      "price": "0.5",
      "size": "200",
      "side": "BUY",
      "hash": "...",
      "best_bid": "0.5",
      "best_ask": "1"
    }
  ],
  "timestamp": "1757908892351"
}
```

### Last Trade Price Event

```json
{
  "event_type": "last_trade_price",
  "asset_id": "TOKEN_ID",
  "market": "0x...",
  "price": "0.456",
  "side": "BUY",
  "size": "219.217767",
  "fee_rate_bps": "0",
  "timestamp": "1750428146322"
}
```

### Market Resolved Event (Custom Feature)

```json
{
  "event_type": "market_resolved",
  "id": "1031769",
  "question": "Will NVIDIA close above $240?",
  "market": "0x...",
  "winning_asset_id": "TOKEN_ID",
  "winning_outcome": "Yes",
  "timestamp": "1766790415550"
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
  "auth": {
    "apiKey": "your-api-key",
    "secret": "your-api-secret",
    "passphrase": "your-passphrase"
  },
  "markets": ["CONDITION_ID_1", "CONDITION_ID_2"],
  "type": "user"
}
```

**Note**: User channel subscribes by **condition IDs** (not asset IDs). Dynamic subscribe/unsubscribe uses `"markets"` field with `"operation"` key.

### User Events

| Type | Subtypes | Description |
|------|----------|-------------|
| `trade` | MATCHED → MINED → CONFIRMED (or RETRYING → FAILED) | Trade lifecycle |
| `order` | PLACEMENT, UPDATE, CANCELLATION | Order events |

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

### Heartbeat / Keepalive

**Market & User channels**: Send `PING` every 10 seconds; server responds with `PONG`.

**Sports channel**: Server sends `ping` every 5 seconds; respond with `pong` within 10 seconds or get disconnected.

### Key Points

- Send `PING` every 10s for market/user channels (not WebSocket ping frames — literal text `PING`)
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
