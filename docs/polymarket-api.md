# Polymarket CLOB API Reference

> Complete reference for the Polymarket Central Limit Order Book (CLOB) REST API.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [GET /markets](#get-markets)
  - [GET /book](#get-book)
  - [POST /order](#post-order)
  - [POST /orders (batch)](#post-orders-batch)
  - [DELETE /order](#delete-order)
  - [DELETE /cancel-market-orders](#delete-cancel-market-orders)
- [Order Types](#order-types)
- [Signature Types](#signature-types)
- [Tick Sizes & Neg Risk](#tick-sizes--neg-risk)
- [Fee Rates](#fee-rates)
- [Rate Limits](#rate-limits)
- [Error Codes](#error-codes)
- [py-clob-client Library](#py-clob-client-library)

---

## Base URL

```
https://clob.polymarket.com
```

All endpoints are relative to this base.

## Authentication

Polymarket uses a three-part authentication system:

| Component | Description |
|-----------|-------------|
| **API Key** | Your public identifier |
| **API Secret** | Used to sign requests (HMAC) |
| **Passphrase** | Additional auth factor set during key creation |

### L1 vs L2 Authentication

- **L1 Auth**: Used for read-only operations and API key management. Requires signing a message with your Ethereum private key.
- **L2 Auth**: Used for order placement/cancellation. Requires CLOB API key + secret + passphrase headers.

### L2 Auth Headers

Every authenticated request includes:

```
POLY_ADDRESS: 0xYOUR_WALLET
POLY_SIGNATURE: <HMAC signature>
POLY_TIMESTAMP: <unix timestamp>
POLY_NONCE: <random nonce>
POLY_API_KEY: YOUR_API_KEY
POLY_PASSPHRASE: YOUR_PASSPHRASE
```

The signature is an HMAC-SHA256 of `timestamp + method + path + body` using your API secret.

### Creating API Keys

```python
from py_clob_client.client import ClobClient

client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,  # Polygon
    key="YOUR_PRIVATE_KEY",
)

# Derive L1 credentials
client.set_api_creds(client.create_or_derive_api_creds())
```

---

## Endpoints

### GET /markets

Retrieve available markets.

```
GET https://clob.polymarket.com/markets?next_cursor=<cursor>
```

**Response:**
```json
{
  "data": [
    {
      "condition_id": "0x...",
      "question": "Will BTC be above $50,000?",
      "tokens": [
        {"token_id": "12345...", "outcome": "Yes"},
        {"token_id": "67890...", "outcome": "No"}
      ],
      "minimum_order_size": 5,
      "minimum_tick_size": 0.01,
      "neg_risk": false,
      "active": true
    }
  ],
  "next_cursor": "abc123"
}
```

**Pagination**: Use `next_cursor` to iterate through all markets.

### GET /book

Get the order book for a specific token.

```
GET https://clob.polymarket.com/book?token_id=<token_id>
```

**Response:**
```json
{
  "market": "0x...",
  "asset_id": "12345...",
  "bids": [
    {"price": "0.52", "size": "100.0"},
    {"price": "0.51", "size": "250.0"}
  ],
  "asks": [
    {"price": "0.53", "size": "150.0"},
    {"price": "0.54", "size": "200.0"}
  ],
  "hash": "0x..."
}
```

### POST /order

Place a single order. Requires L2 authentication.

```
POST https://clob.polymarket.com/order
Content-Type: application/json
```

**Request Body:**
```json
{
  "order": {
    "salt": 12345678,
    "maker": "0xYOUR_WALLET",
    "signer": "0xYOUR_WALLET",
    "taker": "0x0000...0000",
    "tokenId": "12345...",
    "makerAmount": "50000000",
    "takerAmount": "100000000",
    "expiration": "0",
    "nonce": "0",
    "feeRateBps": "0",
    "side": "BUY",
    "signatureType": 0,
    "signature": "0x..."
  },
  "orderType": "GTC",
  "tickSize": "0.01",
  "negRisk": false
}
```

**Response:**
```json
{
  "orderID": "0xabc123...",
  "status": "LIVE",
  "transactionsHashes": []
}
```

**Important**: If `status` is `"MATCHED"`, the order was immediately filled (taker fill). It's done, not pending.

### POST /orders (batch)

Place up to **100 orders** in a single HTTP call.

```
POST https://clob.polymarket.com/orders
Content-Type: application/json
```

**Request Body:**
```json
{
  "orders": [
    { "order": {...}, "orderType": "GTC", "tickSize": "0.01", "negRisk": false },
    { "order": {...}, "orderType": "GTC", "tickSize": "0.01", "negRisk": false }
  ]
}
```

**Performance**: Batch placement takes 0.3-1.3s total vs 4-6s for sequential individual calls.

### DELETE /order

Cancel a single order.

```
DELETE https://clob.polymarket.com/order/{order_id}
```

### DELETE /cancel-market-orders

Cancel all orders for a specific market.

```
DELETE https://clob.polymarket.com/cancel-market-orders
Content-Type: application/json
```

**Request Body:**
```json
{
  "market": "condition_id_here",
  "asset_id": "token_id_here"
}
```

---

## Order Types

| Type | Code | Description |
|------|------|-------------|
| **GTC** | `"GTC"` | Good Till Cancel — stays on book until filled or cancelled |
| **GTD** | `"GTD"` | Good Till Date — expires at specified time |
| **FOK** | `"FOK"` | Fill Or Kill — must fill entirely or is cancelled immediately |

GTC is the most common for market making. FOK is useful for aggressive taking.

## Signature Types

| Type | Value | Description |
|------|-------|-------------|
| **EOA** | `0` | Externally Owned Account — direct wallet signing |
| **Poly Proxy** | `2` | Gnosis Safe / Poly proxy wallet — for funded proxy wallets |

If using a Polymarket-generated proxy wallet (common when depositing via the UI), use `signature_type=2`.

## Tick Sizes & Neg Risk

Each market has specific tick size and neg_risk parameters that **must** be included in order requests.

```python
# Query market parameters
resp = client.get_market(condition_id="0xCONDITION_ID")
tick_size = resp["minimum_tick_size"]  # "0.01" or "0.001"
neg_risk = resp["neg_risk"]            # True or False
```

**Cache these** — they don't change for a given market, and querying per-order wastes rate limit.

## Fee Rates

- **Maker fee**: 0 bps (free) for limit orders that add liquidity
- **Taker fee**: Varies, typically 0-2 bps
- Fee is encoded in the order's `feeRateBps` field

## Rate Limits

- **General**: ~100 requests/second per API key
- **Order placement**: Lower limits apply; batch orders help avoid hitting these
- **WebSocket**: Preferred for reading market data to avoid REST rate limits
- **Error 429**: Too Many Requests — implement exponential backoff

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request — invalid parameters |
| 401 | Unauthorized — auth headers wrong |
| 404 | Not Found — invalid order ID or market |
| 429 | Rate Limited |
| 500 | Server Error — retry with backoff |

---

## py-clob-client Library

The official Python client simplifies authentication and order signing.

### Installation

```bash
pip install py-clob-client
```

### Basic Usage

```python
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

# Initialize client
client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key="YOUR_PRIVATE_KEY",
    signature_type=0,  # 0=EOA, 2=Poly Proxy
)

# Create/derive API credentials
creds = client.create_or_derive_api_creds()
client.set_api_creds(creds)

# Get order book
book = client.get_order_book(token_id="TOKEN_ID_HERE")
print(f"Best bid: {book.bids[0].price}, Best ask: {book.asks[0].price}")

# Place a GTC buy order
order_args = OrderArgs(
    price=0.50,
    size=100.0,
    side="BUY",
    token_id="TOKEN_ID_HERE",
)
signed_order = client.create_order(order_args)
resp = client.post_order(signed_order, OrderType.GTC)
print(f"Order ID: {resp['orderID']}, Status: {resp['status']}")

# Cancel an order
client.cancel(order_id="ORDER_ID_HERE")

# Cancel all orders for a market
client.cancel_market_orders(condition_id="CONDITION_ID_HERE")
```

### Batch Order Placement

```python
# Create multiple signed orders
orders = []
for price in [0.47, 0.48, 0.49]:
    args = OrderArgs(price=price, size=50.0, side="BUY", token_id="UP_TOKEN_ID")
    orders.append(client.create_order(args))

# Submit batch
resp = client.post_orders(orders, OrderType.GTC)
```

---

*See also: [WebSocket Channels](polymarket-websocket.md) · [Order Management](polymarket-orders.md) · [Market Structure](polymarket-markets.md)*
