# Critical Pitfalls & Hard-Won Lessons

> Everything that went wrong so you don't repeat our mistakes.

## Table of Contents

- [Outcome Verification](#1-outcome-verification)
- [Fill Tracking](#2-fill-tracking)
- [Geo-Blocking](#3-geo-blocking)
- [WebSocket Disconnects](#4-websocket-disconnects)
- [Entry Delay](#5-entry-delay)
- [Emergency Cancel](#6-emergency-cancel)
- [Verifier Timing](#7-verifier-timing)
- [Paper vs Live Gap](#8-paper-vs-live-gap)

---

## 1. Outcome Verification

> ⚠️ **THE MOST EXPENSIVE BUG WE ENCOUNTERED**

### The Mistake

Trusting the engine's outcome prediction (based on Chainlink oracle reads or mid-market prices) instead of verifying via the Gamma API.

### What Happened

- Engine predicted "Up" based on price movement → logged as win
- Actual resolution was "Down" → real money lost
- Dashboard showed positive PnL → we kept trading → lost more
- Only discovered when we manually checked USDC balance

### The Fix

```python
# ALWAYS verify outcomes like this:
def verify_outcome(slug: str) -> str:
    resp = httpx.get(f"https://gamma-api.polymarket.com/markets?slug={slug}")
    market = resp.json()[0]
    
    # STEP 1: Is it actually resolved?
    if market.get("umaResolutionStatus") != "resolved":
        raise ValueError("Market not yet resolved — DO NOT trust any outcome")
    
    # STEP 2: Read the official outcome
    for outcome, price in zip(market["outcomes"], market["outcomePrices"]):
        if price == "1":
            return outcome
    
    raise ValueError("No winning outcome found")
```

### Rules

1. **NEVER** use mid-market prices to determine outcomes
2. **NEVER** trust engine predictions without Gamma API confirmation
3. **ALWAYS** check `umaResolutionStatus == "resolved"` first
4. **ALWAYS** cross-check PnL against actual balance changes

---

## 2. Fill Tracking

### The Mistake

Only tracking fills from one source (POST response OR User WebSocket) instead of both.

### The Problem

- **Taker fills**: Come immediately in the POST /order response (`status: "MATCHED"`)
- **Maker fills**: Come asynchronously via the User WebSocket (`event_type: "trade"`)

If you only track POST responses, you miss every maker fill. If you only track WebSocket, you miss taker fills (they may not always appear on WS).

### The Fix

Track both sources. Deduplicate by order_id.

```python
class FillTracker:
    def __init__(self):
        self.fills = {}  # order_id -> fill details
    
    def on_post_response(self, resp):
        if resp["status"] == "MATCHED":
            self.fills[resp["orderID"]] = {"source": "taker", ...}
    
    def on_ws_trade(self, msg):
        if msg["event_type"] == "trade":
            oid = msg["order_id"]
            if oid not in self.fills:  # Don't double-count
                self.fills[oid] = {"source": "maker", ...}
```

---

## 3. Geo-Blocking

### The Problem

Polymarket blocks access from many countries/regions. If you're in a restricted region:
- REST API calls return 403
- WebSocket connections are refused
- The website itself is blocked

### Geoblock Check Endpoint

```
GET https://polymarket.com/api/geoblock
→ {"blocked": true, "ip": "...", "country": "US", "region": "NY"}
```

### Blocked Countries (as of Feb 2026)

**Fully blocked**: US, AU, BE, BY, BI, CF, CD, CU, DE, ET, FR, GB, IR, IQ, IT, KP, LB, LY, MM, NI, NL, RU, SO, SS, SD, SY, UM, VE, YE, ZW

**Close-only** (can close positions, cannot open new): PL, SG, TH, TW

**Blocked regions**: Canada/Ontario, Ukraine (Crimea, Donetsk, Luhansk)

### The Fix

Use a proxy in a non-restricted region.

```python
import httpx

client = httpx.Client(proxy="socks5://YOUR_PROXY_HOST:YOUR_PROXY_PORT")
```

### Important Notes

- Binance also has geo-restrictions (different regions than Polymarket)
- You may need **different proxies** for Polymarket and Binance
- Test proxy connectivity before deploying live trading
- Proxy latency adds to your order execution time

---

## 4. WebSocket Disconnects

### The Problem

WebSocket connections drop. Always. Causes:
- Network hiccups
- Server-side disconnections
- Idle timeouts
- Proxy issues

### What Goes Wrong

- Miss fills → incorrect position tracking → wrong PnL
- Miss price updates → stale book data → bad order placement
- Miss market events → don't know when trading window ends

### The Fix

```python
# 1. Automatic reconnection with exponential backoff
# 2. Re-subscribe after reconnection
# 3. Request fresh state (book snapshot) after reconnecting
# 4. Preserve local state across reconnections

async def robust_ws(url, subscribe_msg, handler, state):
    backoff = 1
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                backoff = 1
                await ws.send(json.dumps(subscribe_msg))
                
                async for raw in ws:
                    msg = json.loads(raw)
                    await handler(msg, state)
                    
        except Exception as e:
            print(f"WS error: {e}, reconnecting in {backoff}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
```

---

## 5. Entry Delay

### The Problem

In 5-minute BTC markets, entering late is extremely costly.

### Why

- **0-30s**: Market is fresh. Prices are near 50/50. Spread is wide. Good time to place orders.
- **30-120s**: BTC is moving. Polymarket prices start reflecting the move. Still okay.
- **120-240s**: Prices have largely moved. Entering now = buying at worse prices with less time to pair.
- **240-300s**: Prices converging to outcome. Extremely dangerous.

### The Data

Markets where we entered >30s late had significantly worse PnL than early entries, even with the same strategy parameters.

### The Fix

- Detect new markets ASAP (poll or WebSocket)
- Pre-compute order parameters before market opens
- Use batch orders for fast placement
- If >30s late, consider skipping the market entirely

---

## 6. Emergency Cancel

### The Dilemma

When the market is about to close, should you cancel all open orders?

**With emergency cancel**:
- ✅ Prevents last-second adverse fills
- ❌ May cancel orders that would have profitably filled
- ❌ Reduces overall fill rate

**Without emergency cancel**:
- ✅ More fills (some profitable)
- ❌ Last-second fills often adverse (price has converged to outcome)
- ❌ Leaves uncontrolled exposure

### What We Learned

- Emergency cancel at T-30s was too early — missed profitable fills
- Emergency cancel at T-10s was too late — adverse fills already happened
- No emergency cancel at all — worst results (uncontrolled last-second fills)
- **T-20s** was the sweet spot in our testing, but YMMV

---

## 7. Verifier Timing

### The Problem

Checking the Gamma API for outcome **too early** after market close returns incorrect data.

### What Happens

1. Market closes at T=300s
2. You check Gamma API at T=301s
3. `umaResolutionStatus` is still `"proposed"` or `null`
4. `outcomePrices` might be `["0.5", "0.5"]` or stale values
5. You use these → wrong outcome → wrong PnL tracking

### The Fix

```python
async def wait_for_resolution(slug: str, timeout: int = 120) -> str:
    """Wait for market to be fully resolved."""
    start = time.time()
    
    while time.time() - start < timeout:
        resp = httpx.get(f"https://gamma-api.polymarket.com/markets?slug={slug}")
        market = resp.json()[0]
        
        if market.get("umaResolutionStatus") == "resolved":
            for outcome, price in zip(market["outcomes"], market["outcomePrices"]):
                if price == "1":
                    return outcome
        
        await asyncio.sleep(5)  # Check every 5 seconds
    
    raise TimeoutError(f"Market {slug} not resolved within {timeout}s")
```

---

## 8. Paper vs Live Gap

### The Problem

Paper trading results are systematically more optimistic than live results.

### Quantified Differences

| Metric | Paper | Live |
|--------|-------|------|
| Fill rate | ~80% | ~40-60% |
| Adverse fills | ~5% | ~30% |
| Pair completion | ~70% | ~30-50% |
| PnL per market | +$1.30 | -$0.80 |

### Why

1. **No queue position**: Paper fills assume you're first in queue. In reality, other market makers are ahead of you.
2. **No adverse selection**: Paper fills at your price. Live fills often happen because someone with better information is taking the other side.
3. **No partial fills**: Paper fills full size. Live often fills partial.
4. **No latency**: Paper fills instantly. Live has network + matching delay.
5. **No competition**: Paper assumes static order book. Live has other bots competing.

### The Lesson

Divide paper trading profits by **at least 3-5×** to estimate live performance. If your paper strategy isn't profitable by >3×, it will almost certainly lose money live.

---

## 9. Matching Engine Restarts

The CLOB matching engine periodically restarts. During restarts:
- Order placement returns **HTTP 425 (Too Early)**
- Existing orders remain intact
- Retry with exponential backoff until the engine is back

**Handle this in your code**: Always catch 425 responses and retry.

---

## 10. Fee-Enabled Markets

Since Jan-Feb 2026, some markets charge taker fees (5-min crypto, 15-min crypto, NCAAB, Serie A). If you don't include `feeRateBps` in your signed order, it will be rejected on fee-enabled markets. The SDKs handle this automatically — if using REST directly, always query `/fee-rate` first.

---

*See also: [Strategies Tested](strategies-tested.md) · [Market Structure](polymarket-markets.md) · [Architecture Patterns](architecture-patterns.md)*
