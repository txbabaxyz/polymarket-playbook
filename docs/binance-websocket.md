# Binance WebSocket Feeds

> Real-time BTC price data from Binance spot and futures markets.

## Table of Contents

- [Overview](#overview)
- [Spot Trade Stream](#spot-trade-stream)
- [Spot Book Ticker](#spot-book-ticker)
- [Futures Aggregate Trade](#futures-aggregate-trade)
- [Futures Book Ticker](#futures-book-ticker)
- [Combined Streams](#combined-streams)
- [Proxy Requirements](#proxy-requirements)
- [Reconnection & Keepalive](#reconnection--keepalive)
- [Calculating Metrics](#calculating-metrics)

---

## Overview

Binance provides free, unauthenticated WebSocket streams for market data. These are the primary signal source for BTC-related Polymarket strategies.

| Stream | URL | Use Case |
|--------|-----|----------|
| Spot Trade | `wss://stream.binance.com:9443/ws/btcusdt@trade` | Individual trade execution data |
| Spot Book Ticker | `wss://stream.binance.com:9443/ws/btcusdt@bookTicker` | Best bid/ask (fastest) |
| Futures Agg Trade | `wss://fstream.binance.com/ws/btcusdt@aggTrade` | Aggregated futures trades |
| Futures Book Ticker | `wss://fstream.binance.com/ws/btcusdt@bookTicker` | Futures best bid/ask |

---

## Spot Trade Stream

```
wss://stream.binance.com:9443/ws/btcusdt@trade
```

Every individual trade on BTCUSDT spot.

### Message Format

```json
{
  "e": "trade",
  "E": 1700000000123,
  "s": "BTCUSDT",
  "t": 123456789,
  "p": "50000.50",
  "q": "0.001",
  "b": 111111,
  "a": 222222,
  "T": 1700000000100,
  "m": true,
  "M": true
}
```

| Field | Description |
|-------|-------------|
| `e` | Event type |
| `E` | Event time (ms) |
| `p` | Price |
| `q` | Quantity |
| `T` | Trade time (ms) |
| `m` | Is buyer the market maker? (`true` = sell/down-tick, `false` = buy/up-tick) |

### Interpreting `m` (maker side)

- `m: true` → The buyer was the **maker** → The trade was initiated by a **seller** (aggressive sell)
- `m: false` → The seller was the **maker** → The trade was initiated by a **buyer** (aggressive buy)

This is critical for computing **Order Flow Imbalance (OFI)**.

---

## Spot Book Ticker

```
wss://stream.binance.com:9443/ws/btcusdt@bookTicker
```

The **fastest** way to track BTC price. Updates on every best bid/ask change.

### Message Format

```json
{
  "u": 400900217,
  "s": "BTCUSDT",
  "b": "50000.10",
  "B": "1.500",
  "a": "50000.20",
  "A": "2.300"
}
```

| Field | Description |
|-------|-------------|
| `b` | Best bid price |
| `B` | Best bid quantity |
| `a` | Best ask price |
| `A` | Best ask quantity |

---

## Futures Aggregate Trade

```
wss://fstream.binance.com/ws/btcusdt@aggTrade
```

Aggregated trade stream from BTCUSDT perpetual futures. Higher volume than spot.

### Message Format

```json
{
  "e": "aggTrade",
  "E": 1700000000123,
  "s": "BTCUSDT",
  "a": 123456789,
  "p": "50000.50",
  "q": "0.500",
  "f": 100000,
  "l": 100005,
  "T": 1700000000100,
  "m": true
}
```

| Field | Description |
|-------|-------------|
| `a` | Aggregate trade ID |
| `p` | Price |
| `q` | Quantity |
| `f` | First trade ID in aggregation |
| `l` | Last trade ID in aggregation |
| `T` | Trade time (ms) |
| `m` | Is buyer the maker? |

---

## Futures Book Ticker

```
wss://fstream.binance.com/ws/btcusdt@bookTicker
```

Same format as spot book ticker but for the futures market. Often leads spot by milliseconds.

---

## Combined Streams

Subscribe to multiple streams in one connection:

```
wss://stream.binance.com:9443/stream?streams=btcusdt@trade/btcusdt@bookTicker
```

Or for futures:
```
wss://fstream.binance.com/stream?streams=btcusdt@aggTrade/btcusdt@bookTicker
```

### Combined Message Format

Messages are wrapped:

```json
{
  "stream": "btcusdt@trade",
  "data": {
    "e": "trade",
    "p": "50000.50",
    ...
  }
}
```

Route by `msg["stream"]` to the appropriate handler.

---

## Proxy Requirements

> ⚠️ Binance blocks connections from many regions (US, and others).

If you're running from a geo-restricted location, you need a proxy:

```python
import websockets

# Direct connection (may be blocked)
ws = await websockets.connect("wss://stream.binance.com:9443/ws/btcusdt@trade")

# Via SOCKS5 proxy
import socks
# Configure your proxy: YOUR_PROXY_HOST:YOUR_PROXY_PORT
```

For `httpx` or `aiohttp`, configure the proxy in the client:

```python
import httpx

# REST API calls through proxy
client = httpx.Client(proxy="socks5://YOUR_PROXY_HOST:YOUR_PROXY_PORT")
```

---

## Reconnection & Keepalive

### Binance WebSocket Behavior

- Connections are dropped after **24 hours** by Binance
- A single `ping` frame is sent every 3 minutes; you must respond with `pong`
- If no `pong` within 10 minutes, connection is terminated

### Robust Connection Pattern

```python
import asyncio
import websockets
import json

async def binance_stream(url: str, handler):
    """Connect to Binance WS with auto-reconnection."""
    backoff = 1

    while True:
        try:
            async with websockets.connect(url, ping_interval=60, ping_timeout=30) as ws:
                backoff = 1
                async for raw in ws:
                    msg = json.loads(raw)
                    await handler(msg)

        except (websockets.ConnectionClosed, ConnectionError) as e:
            print(f"Binance WS disconnected: {e}. Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
```

---

## Calculating Metrics

### VWAP (Volume-Weighted Average Price)

```python
def calculate_vwap(trades: list[dict]) -> float:
    """Calculate VWAP from a window of trades."""
    total_volume = sum(float(t["q"]) for t in trades)
    if total_volume == 0:
        return 0.0
    return sum(float(t["p"]) * float(t["q"]) for t in trades) / total_volume
```

### Order Flow Imbalance (OFI)

```python
def calculate_ofi(trades: list[dict]) -> float:
    """
    OFI > 0 = more aggressive buying (bullish).
    OFI < 0 = more aggressive selling (bearish).
    """
    buy_volume = sum(float(t["q"]) for t in trades if not t["m"])
    sell_volume = sum(float(t["q"]) for t in trades if t["m"])
    total = buy_volume + sell_volume
    if total == 0:
        return 0.0
    return (buy_volume - sell_volume) / total
```

### Volume Surge Detection

```python
def detect_volume_surge(
    recent_volume: float,
    baseline_volume: float,
    threshold: float = 2.0,
) -> bool:
    """Detect if recent volume is significantly above baseline."""
    if baseline_volume == 0:
        return False
    return (recent_volume / baseline_volume) > threshold
```

### Book Imbalance

```python
def book_imbalance(bid_qty: float, ask_qty: float) -> float:
    """
    Positive = more bid pressure (bullish).
    Negative = more ask pressure (bearish).
    Range: -1.0 to 1.0
    """
    total = bid_qty + ask_qty
    if total == 0:
        return 0.0
    return (bid_qty - ask_qty) / total
```

---

*See also: [Metrics & Calculations](metrics-calculations.md) · [Architecture Patterns](architecture-patterns.md)*
