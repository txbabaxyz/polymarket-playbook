# Polymarket API Reference

> Complete reference for all three Polymarket APIs: Gamma, Data, and CLOB.

## Table of Contents

- [Three APIs Overview](#three-apis-overview)
- [Base URLs](#base-urls)
- [Authentication](#authentication)
- [Gamma API (Markets & Events)](#gamma-api-markets--events)
- [Data API (Positions & Trades)](#data-api-positions--trades)
- [CLOB API (Orderbook & Trading)](#clob-api-orderbook--trading)
  - [Market Data Endpoints](#market-data-endpoints)
  - [Trading Endpoints](#trading-endpoints)
- [Bridge API](#bridge-api)
- [Order Types](#order-types)
- [Signature Types](#signature-types)
- [Tick Sizes & Neg Risk](#tick-sizes--neg-risk)
- [Fee Rates](#fee-rates)
- [Rate Limits](#rate-limits)
- [Error Codes](#error-codes)
- [SDKs & Client Libraries](#sdks--client-libraries)

---

## Three APIs Overview

Polymarket is served by **three separate APIs**, each handling a different domain:

| API | Base URL | Auth Required | Purpose |
|-----|----------|---------------|---------|
| **Gamma API** | `https://gamma-api.polymarket.com` | No | Markets, events, tags, series, comments, sports, search, profiles |
| **Data API** | `https://data-api.polymarket.com` | No | User positions, trades, activity, holders, open interest, leaderboards |
| **CLOB API** | `https://clob.polymarket.com` | Partial (trading only) | Orderbook, pricing, order placement/cancellation, heartbeat |
| **Bridge API** | `https://bridge.polymarket.com` | No | Deposits & withdrawals (proxy for fun.xyz) |

---

## Base URLs

```
Gamma:  https://gamma-api.polymarket.com
Data:   https://data-api.polymarket.com
CLOB:   https://clob.polymarket.com
Bridge: https://bridge.polymarket.com
```

---

## Authentication

### Public vs Authenticated

- **Gamma API** and **Data API**: Fully public — no auth required
- **CLOB read endpoints** (orderbook, prices, spreads): No auth required
- **CLOB trading endpoints** (orders, cancellations, heartbeat): Require L2 auth headers

### Two-Level Auth Model

| Level | Method | Used For |
|-------|--------|----------|
| **L1** | EIP-712 signed message with private key | Creating/deriving API credentials, signing orders |
| **L2** | HMAC-SHA256 with API credentials | Authenticating trading API requests |

### L1 Auth Headers (Key Management)

```
POLY_ADDRESS:   0xYOUR_WALLET
POLY_SIGNATURE: <EIP-712 signature>
POLY_TIMESTAMP: <unix timestamp>
POLY_NONCE:     <nonce, default 0>
```

### L2 Auth Headers (Trading)

```
POLY_ADDRESS:    0xYOUR_WALLET
POLY_SIGNATURE:  <HMAC-SHA256 signature>
POLY_TIMESTAMP:  <unix timestamp>
POLY_API_KEY:    <your apiKey>
POLY_PASSPHRASE: <your passphrase>
```

The HMAC signature is computed over `timestamp + method + path + body` using your API `secret`.

### Creating API Credentials

```python
from py_clob_client.client import ClobClient

client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key="YOUR_PRIVATE_KEY",
)
creds = client.create_or_derive_api_creds()
# Returns: { apiKey, secret, passphrase }
```

### REST API Key Endpoints

```
POST https://clob.polymarket.com/auth/api-key     # Create new credentials
GET  https://clob.polymarket.com/auth/derive-api-key  # Derive existing credentials
```

---

## Gamma API (Markets & Events)

Base: `https://gamma-api.polymarket.com`

### Markets

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/markets` | GET | List markets (paginated, filterable) |
| `/markets/{id}` | GET | Get market by condition ID |
| `/markets?slug={slug}` | GET | Get market by slug |
| `/markets/{id}/tags` | GET | Get tags for a market |
| `/markets/sampling` | GET | Get sampling markets (random subset) |
| `/markets/simplified` | GET | Get simplified market objects |
| `/markets/sampling/simplified` | GET | Sampling + simplified |

### Events

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events` | GET | List events (paginated) |
| `/events/{id}` | GET | Get event by ID |
| `/events?slug={slug}` | GET | Get event by slug |
| `/events/{id}/tags` | GET | Get event tags |

### Tags, Series, Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tags` | GET | List all tags |
| `/tags/{id}` | GET | Get tag by ID |
| `/tags?slug={slug}` | GET | Get tag by slug |
| `/tags/{id}/related` | GET | Get related tags |
| `/series` | GET | List series |
| `/series/{id}` | GET | Get series by ID |
| `/public-search?query=...` | GET | Search markets, events, profiles |

### Comments & Profiles

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/comments` | GET | List comments (by market, user, or ID) |
| `/comments/{id}` | GET | Get comment by ID |
| `/profiles/{address}` | GET | Get public profile by wallet address |

### Sports

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sports/metadata` | GET | Sports metadata |
| `/sports/market-types` | GET | Valid sports market types |
| `/sports/teams` | GET | List teams |

### Prices History

```
GET https://gamma-api.polymarket.com/markets/{condition_id}/prices-history?interval=max&fidelity=60
```

---

## Data API (Positions & Trades)

Base: `https://data-api.polymarket.com`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/positions?user={address}` | GET | Current positions for a user |
| `/closed-positions?user={address}` | GET | Closed positions |
| `/positions?market={condition_id}` | GET | Positions for a market |
| `/top-holders?market={condition_id}` | GET | Top holders for a market |
| `/portfolio-value?user={address}` | GET | Total value of user's positions |
| `/trades?user={address}` | GET | Trades for a user |
| `/trades?market={condition_id}` | GET | Trades for a market |
| `/activity?user={address}` | GET | User activity |
| `/leaderboard` | GET | Trader leaderboard rankings |
| `/open-interest?market={condition_id}` | GET | Open interest for a market |
| `/volume?event_id={id}` | GET | Live volume for an event |
| `/total-markets-traded?user={address}` | GET | Total markets a user has traded |
| `/accounting-snapshot?user={address}` | GET | Download ZIP of CSV accounting data |

### Builder Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/builders/leaderboard` | GET | Aggregated builder leaderboard |
| `/builders/volume-timeseries` | GET | Daily builder volume time-series |

---

## CLOB API (Orderbook & Trading)

Base: `https://clob.polymarket.com`

### Market Data Endpoints (Public — No Auth)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/book?token_id={id}` | GET | Order book for a token |
| `/books` | POST | Batch order books (body: token IDs) |
| `/price?token_id={id}&side={BUY\|SELL}` | GET | Best market price |
| `/prices` | GET/POST | Batch market prices |
| `/midpoint?token_id={id}` | GET | Midpoint price (avg best bid/ask) |
| `/midpoints` | GET/POST | Batch midpoints (max 500 tokens) |
| `/spread?token_id={id}` | GET | Spread (best ask - best bid) |
| `/spreads` | GET/POST | Batch spreads |
| `/last-trade-price?token_id={id}` | GET | Last trade price and side |
| `/last-trade-prices` | GET/POST | Batch last trade prices (max 500) |
| `/tick-size?token_id={id}` | GET | Minimum tick size |
| `/tick-size/{token_id}` | GET | Tick size (path parameter) |
| `/fee-rate?token_id={id}` | GET | Fee rate for a token |
| `/fee-rate/{token_id}` | GET | Fee rate (path parameter) |
| `/prices-history` | GET | Historical price data |
| `/markets?next_cursor={cursor}` | GET | CLOB market list (paginated) |
| `/time` | GET | Server time (Unix timestamp) |

### Trading Endpoints (Require L2 Auth)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/order` | POST | Place single order |
| `/orders` | POST | Place batch orders (max 15) |
| `/order/{id}` | DELETE | Cancel single order |
| `/orders` | DELETE | Cancel multiple orders (max 3000) |
| `/cancel-all` | DELETE | Cancel all open orders |
| `/cancel-market-orders` | DELETE | Cancel all orders for a market+asset |
| `/order/{id}` | GET | Get single order by ID |
| `/orders` | GET | Get user's open orders (paginated) |
| `/trades` | GET | Get user's trades (paginated) |
| `/heartbeat` | POST | Send heartbeat (prevents auto-cancel) |
| `/order-scoring/{id}` | GET | Check if order is scoring for rewards |

#### POST /order — Place Single Order

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

**Statuses**: `live` (resting), `matched` (immediately filled), `delayed` (sports 3s delay), `unmatched` (delayed order placed on book).

#### POST /orders — Batch Orders (Max 15 per request)

Orders processed in parallel. Each gets individual status.

#### Heartbeat

If heartbeats are enabled and not sent regularly, **all open orders are auto-cancelled**. Useful for automated systems that need a dead-man's switch.

```
POST /heartbeat
```

---

## Bridge API

Base: `https://bridge.polymarket.com` (proxies fun.xyz)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/deposit-addresses` | POST | Create deposit addresses |
| `/withdrawal-addresses` | POST | Create withdrawal addresses |
| `/quote` | GET | Get fee/output quote for bridge |
| `/supported-assets` | GET | List supported chains and tokens |
| `/transaction-status/{id}` | GET | Track bridge transaction status |

---

## Order Types

| Type | Code | Description |
|------|------|-------------|
| **GTC** | `"GTC"` | Good Till Cancel — rests on book until filled or cancelled |
| **GTD** | `"GTD"` | Good Till Date — auto-expires at specified time |
| **FOK** | `"FOK"` | Fill Or Kill — fill entirely or reject immediately |
| **FAK** | `"FAK"` | Fill And Kill — fill what's available, cancel the rest |

**Post-Only**: Orders that would cross the spread are rejected (guarantees maker status).

## Signature Types

| Type | Value | Description |
|------|-------|-------------|
| **EOA** | `0` | Standard Ethereum wallet. Funder = EOA address, needs POL for gas. |
| **POLY_PROXY** | `1` | Magic Link proxy wallet. Requires exported PK from Polymarket.com. |
| **GNOSIS_SAFE** | `2` | Gnosis Safe multisig proxy (most common for new users). |

The wallet address on Polymarket.com is the **proxy wallet** (funder). Use it as the `funder` parameter.

## Tick Sizes & Neg Risk

Each market has specific tick size and neg_risk parameters that **must** be included in order requests.

```python
resp = client.get_market(condition_id="0xCONDITION_ID")
tick_size = resp["minimum_tick_size"]  # "0.01" or "0.001"
neg_risk = resp["neg_risk"]            # True or False
```

**Tick size changes dynamically**: When price > 0.96 or < 0.04, tick size changes from 0.01 to 0.001.

## Fee Rates

### Fee-Free Markets (Most Markets)

No trading fees. No deposit/withdrawal fees from Polymarket (intermediaries may charge).

### Markets With Taker Fees

- **5-minute crypto markets**
- **15-minute crypto markets**
- **NCAAB (college basketball) markets** (from Feb 18, 2026)
- **Serie A markets** (from Feb 18, 2026)

### Fee Formula

```
fee = C × feeRate × (p × (1 - p))^exponent
```

| Parameter | Sports (NCAAB, Serie A) | 5-Min & 15-Min Crypto |
|-----------|------------------------|----------------------|
| Fee Rate | 0.0175 | 0.25 |
| Exponent | 1 | 2 |
| Maker Rebate % | 25% | 20% |

**Peak effective rate**: 1.56% at p=0.50 for crypto; 0.44% at p=0.50 for sports. Fees are rounded to 4 decimal places.

SDKs automatically fetch and include `feeRateBps` in signed orders. If using REST directly, query `/fee-rate` first.

## Rate Limits

All limits enforced via Cloudflare throttling (sliding windows, requests are delayed not rejected).

### General
| Endpoint | Limit |
|----------|-------|
| General | 15,000 req / 10s |
| Health `/ok` | 100 req / 10s |

### Gamma API
| Endpoint | Limit |
|----------|-------|
| General | 4,000 req / 10s |
| `/events` | 500 req / 10s |
| `/markets` | 300 req / 10s |
| `/markets` + `/events` listing | 900 req / 10s |
| `/comments` | 200 req / 10s |
| `/tags` | 200 req / 10s |
| `/public-search` | 350 req / 10s |

### Data API
| Endpoint | Limit |
|----------|-------|
| General | 1,000 req / 10s |
| `/trades` | 200 req / 10s |
| `/positions` | 150 req / 10s |
| `/closed-positions` | 150 req / 10s |

### CLOB API
| Category | Endpoint | Limit |
|----------|----------|-------|
| General | — | 9,000 req / 10s |
| Book | `/book` | 1,500 req / 10s |
| Book batch | `/books` | 500 req / 10s |
| Price | `/price` | 1,500 req / 10s |
| Price batch | `/prices` | 500 req / 10s |
| Midpoint | `/midpoint` | 1,500 req / 10s |
| Midpoint batch | `/midpoints` | 500 req / 10s |
| Price history | `/prices-history` | 1,000 req / 10s |
| Tick size | — | 200 req / 10s |
| Ledger | `/trades`, `/orders`, `/order` | 900 req / 10s |
| Auth | API key endpoints | 100 req / 10s |

### CLOB Trading (Burst + Sustained)
| Endpoint | Burst (10s) | Sustained (10min) |
|----------|-------------|-------------------|
| `POST /order` | 3,500 | 36,000 |
| `DELETE /order` | 3,000 | 30,000 |
| `POST /orders` | 1,000 | 15,000 |
| `DELETE /orders` | 1,000 | 15,000 |
| `DELETE /cancel-all` | 250 | 6,000 |
| `DELETE /cancel-market-orders` | 1,000 | 1,500 |

### Other
| Endpoint | Limit |
|----------|-------|
| Relayer `/submit` | 25 req / 1 min |
| User PNL API | 200 req / 10s |

## Error Codes

All errors return `{"error": "<message>"}`.

### Global Errors
| Code | Error | Description |
|------|-------|-------------|
| 401 | `Unauthorized/Invalid api key` | Missing/invalid API key |
| 401 | `Invalid L1 Request headers` | HMAC signature mismatch |
| 429 | `Too Many Requests` | Rate limited — exponential backoff |
| 503 | `Trading is currently disabled` | Exchange paused entirely |
| 503 | `Trading is currently cancel-only` | Can cancel but not place orders |

### Order Errors
| Code | Error | Description |
|------|-------|-------------|
| 400 | `invalid post-only order: order crosses book` | Post-only order would match immediately |
| 400 | `Price breaks minimum tick size rule` | Price doesn't align with tick size |
| 400 | `Size lower than the minimum` | Order too small |
| 400 | `not enough balance / allowance` | Insufficient USDC.e or token allowance |
| 400 | `invalid nonce` | Nonce already used |
| 400 | `FOK orders are fully filled or killed` | FOK couldn't be completely filled |
| 400 | `no orders found to match with FAK order` | FAK found zero matches |
| 425 | (Too Early) | Matching engine restarting — retry with backoff |

---

## SDKs & Client Libraries

### Official SDKs

| Language | Package | Repository |
|----------|---------|------------|
| TypeScript | `@polymarket/clob-client` | [github.com/Polymarket/clob-client](https://github.com/Polymarket/clob-client) |
| Python | `py-clob-client` | [github.com/Polymarket/py-clob-client](https://github.com/Polymarket/py-clob-client) |
| Rust | `polymarket-client-sdk` | [github.com/Polymarket/rs-clob-client](https://github.com/Polymarket/rs-clob-client) |

### Builder SDKs (for Builder Program apps)

| Language | Package |
|----------|---------|
| TypeScript | `@polymarket/builder-signing-sdk` |
| Python | `py_builder_signing_sdk` |

### Relayer SDKs (for gasless transactions)

| Language | Package |
|----------|---------|
| TypeScript | `@polymarket/builder-relayer-client` |
| Python | `py-builder-relayer-client` |

### Python Quick Start

```python
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key="YOUR_PRIVATE_KEY",
    signature_type=2,  # GNOSIS_SAFE
    funder="YOUR_PROXY_WALLET",
)
creds = client.create_or_derive_api_creds()
client.set_api_creds(creds)

# Place order
resp = client.create_and_post_order(
    OrderArgs(price=0.50, size=10, side="BUY", token_id="TOKEN_ID"),
    options={"tick_size": "0.01", "neg_risk": False}
)
```

---

*See also: [WebSocket Channels](polymarket-websocket.md) · [Order Management](polymarket-orders.md) · [Market Structure](polymarket-markets.md)*
