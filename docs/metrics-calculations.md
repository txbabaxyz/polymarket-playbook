# Trading Metrics & Calculations

> Mathematical formulas and calculations for Polymarket trading.

## Table of Contents

- [Sigma (σ)](#sigma-σ)
- [Realized Volatility (RV)](#realized-volatility-rv)
- [Order Flow Imbalance (OFI)](#order-flow-imbalance-ofi)
- [VPIN](#vpin)
- [Book Pressure](#book-pressure)
- [Momentum Exhaustion](#momentum-exhaustion)
- [Spread Dynamics](#spread-dynamics)
- [PnL Calculations](#pnl-calculations)
- [Kelly Criterion](#kelly-criterion)

---

## Sigma (σ)

The primary metric for Polymarket market spread efficiency.

```
σ = up_ask + dn_ask
```

| σ Value | Interpretation |
|---------|---------------|
| 1.00 | Perfect — zero spread, no merge edge |
| 1.01-1.03 | Tight — small edge, hard to capture |
| 1.03-1.07 | Normal — typical BTC 5-min markets |
| 1.07-1.10 | Wide — decent edge but lower liquidity |
| > 1.10 | Very wide — usually illiquid or volatile |

### Why Sigma Matters

If σ = 1.05 and you could buy both sides at the ask:
- UP ask: $0.52, DN ask: $0.53 → total $1.05
- Merge return: $1.00
- **Loss**: -$0.05 per pair

σ > 1.0 at the ask means you **lose** money merging at market. The edge comes from getting filled **below** the ask (resting limit orders).

If your average fill prices give you `up_cost + dn_cost < 1.0`, you profit on the merge.

```python
def sigma(up_ask: float, dn_ask: float) -> float:
    """Calculate sigma — market spread efficiency."""
    return up_ask + dn_ask
```

---

## Realized Volatility (RV)

Using the **Parkinson estimator** — more efficient than close-to-close because it uses high/low range.

```
RV_parkinson = sqrt(1 / (4 * n * ln(2)) * Σ(ln(H_i / L_i))²)
```

```python
import math

def parkinson_rv(highs: list[float], lows: list[float]) -> float:
    """
    Parkinson realized volatility estimator.
    
    Args:
        highs: High prices per period
        lows: Low prices per period
    
    Returns:
        Annualized volatility estimate
    """
    n = len(highs)
    if n == 0:
        return 0.0
    
    sum_sq = sum(math.log(h / l) ** 2 for h, l in zip(highs, lows) if l > 0)
    return math.sqrt(sum_sq / (4 * n * math.log(2)))
```

### Application to 5-Min Markets

For BTC 5-minute windows:
- Track high/low from Binance tick data within each 5-min window
- Higher RV → more likely to see large moves → harder to predict direction
- Lower RV → tighter ranges → market prices cluster near 50/50

---

## Order Flow Imbalance (OFI)

Measures the balance between aggressive buying and selling.

```
OFI = (buy_volume - sell_volume) / total_volume
```

| OFI Range | Interpretation |
|-----------|---------------|
| > +0.3 | Strong buying pressure (bullish) |
| +0.1 to +0.3 | Moderate buying |
| -0.1 to +0.1 | Balanced |
| -0.3 to -0.1 | Moderate selling |
| < -0.3 | Strong selling pressure (bearish) |

```python
def ofi(trades: list[dict], window_seconds: float = 30.0) -> float:
    """
    Calculate OFI from Binance trade stream data.
    Uses the 'm' field: m=true → seller-initiated, m=false → buyer-initiated.
    """
    buy_vol = sum(float(t["q"]) for t in trades if not t["m"])
    sell_vol = sum(float(t["q"]) for t in trades if t["m"])
    total = buy_vol + sell_vol
    if total == 0:
        return 0.0
    return (buy_vol - sell_vol) / total
```

---

## VPIN

**Volume-Synchronized Probability of Informed Trading** — detects informed trading activity.

```python
def calculate_vpin(
    trades: list[dict],
    bucket_size: float = 1.0,  # BTC volume per bucket
    n_buckets: int = 50,
) -> float:
    """
    VPIN calculation.
    
    Higher VPIN → more informed trading → higher risk of adverse selection.
    Range: 0.0 to 1.0
    """
    buckets_buy = []
    buckets_sell = []
    current_buy = 0.0
    current_sell = 0.0
    current_volume = 0.0
    
    for trade in trades:
        qty = float(trade["q"])
        is_buy = not trade["m"]
        
        if is_buy:
            current_buy += qty
        else:
            current_sell += qty
        current_volume += qty
        
        if current_volume >= bucket_size:
            buckets_buy.append(current_buy)
            buckets_sell.append(current_sell)
            current_buy = 0.0
            current_sell = 0.0
            current_volume = 0.0
    
    if len(buckets_buy) < n_buckets:
        return 0.0
    
    # Use last n_buckets
    recent_buy = buckets_buy[-n_buckets:]
    recent_sell = buckets_sell[-n_buckets:]
    
    total_volume = sum(b + s for b, s in zip(recent_buy, recent_sell))
    if total_volume == 0:
        return 0.0
    
    order_imbalance = sum(abs(b - s) for b, s in zip(recent_buy, recent_sell))
    return order_imbalance / total_volume
```

---

## Book Pressure

Ratio of bid depth to ask depth — indicates supply/demand imbalance.

```python
def book_pressure(bid_depth: float, ask_depth: float) -> float:
    """
    Book pressure ratio.
    > 1.0 = more bids than asks (support / bullish)
    < 1.0 = more asks than bids (resistance / bearish)
    = 1.0 = balanced
    """
    if ask_depth == 0:
        return float("inf")
    return bid_depth / ask_depth
```

Use with Binance bookTicker `B` (bid qty) and `A` (ask qty) fields.

---

## Momentum Exhaustion

Detecting when a price trend is losing steam.

```python
def momentum_exhaustion(
    prices: list[float],
    window: int = 20,
    threshold: float = 0.3,
) -> bool:
    """
    Detect momentum exhaustion.
    
    Returns True when recent price changes are decelerating
    despite being in a trend.
    """
    if len(prices) < window:
        return False
    
    recent = prices[-window:]
    first_half = recent[:window // 2]
    second_half = recent[window // 2:]
    
    move_first = abs(first_half[-1] - first_half[0])
    move_second = abs(second_half[-1] - second_half[0])
    
    if move_first == 0:
        return False
    
    # Second half moved less than threshold × first half
    return (move_second / move_first) < threshold
```

---

## Spread Dynamics

How Polymarket spreads relate to Binance price movements.

### Key Observation

When BTC makes a sharp move on Binance:
1. The **favored side** (UP if BTC rises) ask tightens as market makers reprice
2. The **unfavored side** (DN if BTC rises) ask widens
3. σ typically **increases** during sharp moves (both sides get more expensive)
4. σ normalizes as the market settles

### Implication for Trading

- Wide σ after a move = opportunity for patient limit orders
- Tight σ = low edge, high competition from other market makers
- σ spikes at market open/close are common

---

## PnL Calculations

### Merge PnL

Profit from merging paired UP + DN tokens.

```
merge_pnl = paired_shares × (1.0 - pair_cost)
```

Where `pair_cost = avg_up_fill_price + avg_dn_fill_price`.

```python
def merge_pnl(paired_shares: int, up_avg_price: float, dn_avg_price: float) -> float:
    """
    Merge PnL — always positive if pair_cost < 1.0.
    
    Example: 100 pairs at UP=$0.47 + DN=$0.50 = $0.97 cost
    merge_pnl = 100 × (1.0 - 0.97) = $3.00
    """
    pair_cost = up_avg_price + dn_avg_price
    return paired_shares * (1.0 - pair_cost)
```

### Settle PnL

PnL from unmatched (unpaired) tokens that are exposed to the outcome.

```python
def settle_pnl(
    unmatched_up: int,
    unmatched_dn: int,
    up_avg_price: float,
    dn_avg_price: float,
    outcome: str,  # "Up" or "Down"
) -> float:
    """
    Settle PnL — can be positive or negative.
    
    If outcome = "Up":
      - UP tokens win: each worth $1.00
      - DN tokens lose: each worth $0.00
    """
    if outcome == "Up":
        up_pnl = unmatched_up * (1.0 - up_avg_price)   # Won
        dn_pnl = unmatched_dn * (0.0 - dn_avg_price)   # Lost
    else:
        up_pnl = unmatched_up * (0.0 - up_avg_price)    # Lost
        dn_pnl = unmatched_dn * (1.0 - dn_avg_price)    # Won
    
    return up_pnl + dn_pnl
```

### Total PnL

```python
def total_pnl(merge: float, settle: float) -> float:
    """Total PnL = merge_pnl + settle_pnl"""
    return merge + settle
```

### The Core Problem

Merge PnL is almost always positive (3-7¢ per pair). But settle PnL is often **negative and larger** because:
- Unmatched tokens are exposed to 50/50 outcomes
- Average loss on wrong-side tokens ≈ cost of those tokens (often $0.45-0.55)
- Even 10 unmatched tokens at $0.50 = potential -$5.00 loss, wiping out 100 pairs of merge profit

---

## Kelly Criterion

Optimal position sizing given your edge and variance.

```
f* = (p × b - q) / b
```

Where:
- `f*` = fraction of bankroll to bet
- `p` = probability of winning
- `q` = probability of losing (1 - p)
- `b` = odds (net payout on a win, expressed as ratio)

```python
def kelly_fraction(win_prob: float, win_amount: float, loss_amount: float) -> float:
    """
    Kelly criterion for position sizing.
    
    Returns optimal fraction of bankroll to risk.
    Negative = don't bet (negative edge).
    """
    if loss_amount == 0:
        return 0.0
    
    b = win_amount / loss_amount  # Odds ratio
    q = 1.0 - win_prob
    
    return (win_prob * b - q) / b


# Example: Strategy with 55% win rate, $3 avg win, $5 avg loss
f = kelly_fraction(0.55, 3.0, 5.0)
# f = (0.55 × 0.6 - 0.45) / 0.6 = (0.33 - 0.45) / 0.6 = -0.20
# Negative! Don't bet — negative expected value despite >50% win rate
```

### Half-Kelly

In practice, use **half-Kelly** (`f* / 2`) for safety — full Kelly is too aggressive and assumes perfect edge estimation.

---

*See also: [Binance WebSocket](binance-websocket.md) · [Strategies Tested](strategies-tested.md) · [Pitfalls](pitfalls.md)*
