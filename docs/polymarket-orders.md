# Polymarket Order Management

> Placing, tracking, and cancelling orders on the CLOB.

## Table of Contents

- [Placing Orders](#placing-orders)
- [Batch Order Placement](#batch-order-placement)
- [Order Tracking](#order-tracking)
- [Fill Detection](#fill-detection)
- [Cancelling Orders](#cancelling-orders)
- [Common Pitfalls](#common-pitfalls)

---

## Placing Orders

### GTC Buy Order

The most common order type for market making:

```python
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key="YOUR_PRIVATE_KEY",
    signature_type=0,
)
client.set_api_creds(client.create_or_derive_api_creds())

# Place a limit buy at $0.48 for 100 shares
order_args = OrderArgs(
    price=0.48,
    size=100.0,
    side="BUY",
    token_id="TOKEN_ID_HERE",
)
signed_order = client.create_order(order_args)
resp = client.post_order(signed_order, OrderType.GTC)

print(f"Order ID: {resp['orderID']}")
print(f"Status: {resp['status']}")  # LIVE or MATCHED
```

### Important Parameters

| Parameter | Notes |
|-----------|-------|
| `price` | Must align with tick size (0.01 or 0.001) |
| `size` | Minimum order size varies by market (typically 5+) |
| `side` | `"BUY"` or `"SELL"` |
| `token_id` | The specific outcome token to trade |

---

## Batch Order Placement

**The single biggest performance optimization.** Instead of placing orders one by one (each taking 0.5-1s), batch up to **15 orders** (official API limit) in one HTTP call.

```python
# Create multiple signed orders
orders = []

# UP side bids at different prices
for price in [0.46, 0.47, 0.48]:
    args = OrderArgs(price=price, size=50.0, side="BUY", token_id="UP_TOKEN_ID")
    orders.append(client.create_order(args))

# DN side bids at different prices
for price in [0.49, 0.50, 0.51]:
    args = OrderArgs(price=price, size=50.0, side="BUY", token_id="DN_TOKEN_ID")
    orders.append(client.create_order(args))

# Submit all 6 orders in one call
resp = client.post_orders(orders, OrderType.GTC)
# Takes 0.3-1.3s total vs ~4-6s sequential
```

### Batch Response

```json
{
  "orderIDs": ["0xAAA...", "0xBBB...", "0xCCC..."],
  "statuses": ["LIVE", "MATCHED", "LIVE"]
}
```

Each order gets its own status. A `MATCHED` status means that specific order was immediately filled.

---

## Order Tracking

### Order Statuses

| Status | Meaning |
|--------|---------|
| `LIVE` | Order is on the book, waiting for a match |
| `MATCHED` | Order has been filled (fully) |
| `CANCELLED` | Order was cancelled (by you or system) |

### Querying Open Orders

```python
# Get all open orders
open_orders = client.get_orders()

# Get orders for a specific market
market_orders = client.get_orders(market="CONDITION_ID")
```

---

## Fill Detection

> ⚠️ **This is a common source of bugs.** Fills come from TWO different sources.

### Source 1: POST Response (Taker Fills)

When you place an order that crosses the spread (your buy price ≥ existing ask), it fills immediately. The POST response tells you:

```json
{
  "orderID": "0xABC...",
  "status": "MATCHED",
  "transactionsHashes": ["0xTXHASH..."]
}
```

`status: "MATCHED"` = the order was filled as a taker. It's done. Do NOT put it in your "pending orders" list.

### Source 2: User WebSocket (Maker Fills)

When you place a limit order that rests on the book (`status: "LIVE"`) and someone later takes it, you receive a fill notification via the User WebSocket:

```json
{
  "event_type": "trade",
  "order_id": "0xDEF...",
  "status": "MATCHED",
  "match_price": "0.50",
  "match_size": "50.0"
}
```

### You MUST Track Both

```python
class FillTracker:
    def __init__(self):
        self.filled = {}  # order_id -> fill details

    def on_post_response(self, resp):
        """Handle taker fills from POST response."""
        if resp["status"] == "MATCHED":
            self.filled[resp["orderID"]] = {
                "source": "taker",
                "price": resp.get("price"),
            }

    def on_ws_fill(self, msg):
        """Handle maker fills from User WebSocket."""
        if msg["event_type"] == "trade" and msg["status"] == "MATCHED":
            self.filled[msg["order_id"]] = {
                "source": "maker",
                "price": msg["match_price"],
                "size": msg["match_size"],
            }
```

---

## Cancelling Orders

### Cancel Single Order

```python
client.cancel(order_id="ORDER_ID_HERE")
```

### Cancel All Orders for a Market

```python
# Cancel all orders for both sides of a market
client.cancel_market_orders(condition_id="CONDITION_ID_HERE")
```

This is essential for **emergency exits** — when you need to pull all orders before a market resolves.

### Cancel Timing

- Cancel requests take 0.1-0.5s typically
- During high volatility, cancels may be slower
- Orders can be filled **between** your cancel request and its execution
- Always check the cancel response to confirm

---

## Common Pitfalls

### 1. MATCHED ≠ Pending

```python
# WRONG — this puts already-filled orders into pending list
resp = client.post_order(signed_order, OrderType.GTC)
pending_orders.append(resp["orderID"])  # Bug if status == "MATCHED"

# RIGHT — check status first
resp = client.post_order(signed_order, OrderType.GTC)
if resp["status"] == "LIVE":
    pending_orders.append(resp["orderID"])
elif resp["status"] == "MATCHED":
    filled_orders.append(resp["orderID"])
```

### 2. Missing Maker Fills

If you only track fills from POST responses, you'll miss every maker fill. Your position tracking will be wrong.

### 3. Tick Size Mismatch

```python
# WRONG — 0.001 tick on a 0.01 market
order_args = OrderArgs(price=0.485, size=100.0, ...)  # Rejected!

# RIGHT — match the market's tick size
order_args = OrderArgs(price=0.48, size=100.0, ...)
```

### 4. Neg Risk Mismatch

The `negRisk` parameter in the order must match the market's `neg_risk` flag. Mismatches cause silent failures.

---

*See also: [CLOB API](polymarket-api.md) · [WebSocket Channels](polymarket-websocket.md) · [Pitfalls](pitfalls.md)*
