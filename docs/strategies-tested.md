# Strategies Tested — What Worked & What Didn't

> Honest documentation of every strategy attempted. Learn from our expensive mistakes.

## 🔴 NONE OF THESE STRATEGIES ARE PROFITABLE IN PRODUCTION. ALL ARCHIVED.

---

## Table of Contents

- [Market Making (Both-Side Ladder)](#market-making-both-side-ladder)
- [SCALPER-CONSERVATIVE](#scalper-conservative)
- [SCALPER-MOMENTUM](#scalper-momentum)
- [SCALPER-MARTINGALE](#scalper-martingale)
- [SCALPER-TURBO](#scalper-turbo)
- [SCALPER-REQUOTE](#scalper-requote)
- [PAIR-HUNTER](#pair-hunter)
- [Signal-Based (v3 Engine)](#signal-based-v3-engine)
- [Key Lessons](#key-lessons)

---

## Market Making (Both-Side Ladder)

**Concept**: Place bids on both UP and DN tokens simultaneously at various price levels. When both sides fill, merge the pairs for guaranteed profit.

**Implementation**:
- Place 3-5 bid levels on each side (e.g., UP at $0.46, $0.47, $0.48; DN at $0.49, $0.50, $0.51)
- Monitor fills via User WebSocket
- When pairs complete, merge for $1.00

**Results**:
- ✅ Merge edge **is real**: 3-7¢ per completed pair
- ❌ **Asymmetric fills destroy profitability**: One side fills much faster than the other
- ❌ Unmatched inventory is exposed to outcome risk → settle losses eat merge profits

**Why It Fails**:
```
Example Market Cycle:
  UP fills: 100 shares at avg $0.47
  DN fills: 30 shares at avg $0.51
  
  Paired: 30 shares → merge_pnl = 30 × (1.0 - 0.98) = $0.60
  Unmatched UP: 70 shares at $0.47
  
  If outcome = "Down":
    settle_pnl = 70 × (0.0 - 0.47) = -$32.90
    
  Total: $0.60 - $32.90 = -$32.30 😱
```

The core problem: when BTC starts moving, one side gets aggressively hit while the other side's orders become stale. You end up long the wrong side.

---

## SCALPER-CONSERVATIVE

**Concept**: Apply quality gates before entering. Only trade when sigma is tight, volume is sufficient, and signals align. Use wide offsets (-3, -4, -5¢ from mid) for safety.

**Parameters**:
- Sigma threshold: σ < 1.06
- Entry offsets: -3¢, -4¢, -5¢ from best ask
- Merge target: 10 pairs before exit
- Buffer time: 60s before market close

**Paper Trading Result**: **+$262** over 200 markets

**Live Result**: **Lost money**

**Why Paper ≠ Live**:
- Paper trading fill model: "if ask ≤ your bid price → fill" — this is wildly optimistic
- Real fills depend on queue position, other market makers, and timing
- In reality, your -3¢ offset orders rarely fill when the market is calm (which is when sigma is tight)
- When they DO fill, it's because the market moved against you (adverse selection)

---

## SCALPER-MOMENTUM

**Concept**: Use Binance price momentum to predict which side will win, then aggressively bid on that side only.

**Parameters**:
- Momentum signal: 30s rolling OFI from Binance futures
- Entry: Bid on favored side when OFI > 0.3
- Exit: Merge if paired, otherwise hold to settlement

**Paper Trading Result**: **+$205** over 150 markets

**Live Result**: **Not validated** — killed after SCALPER-CONSERVATIVE's live failure proved paper results unreliable.

**Analysis**: The momentum signal has some predictive value, but:
- Signal decays rapidly (5-min markets are too short)
- Entry timing is critical — late entry = adverse selection
- Unmatched inventory problem persists

---

## SCALPER-MARTINGALE

**Concept**: After a losing market, double position size on the next market. The theory: eventual wins recover all losses.

**Parameters**:
- Base size: 50 shares
- Multiplier: 2× after each loss
- Max levels: 4 (50 → 100 → 200 → 400)
- Reset: back to 50 after a win

**Paper Trading Result**: **+$134** over 100 markets

**Live Result**: **Never deployed** — too dangerous with real money

**Why It's Dangerous**:
- 4 consecutive losses: 50 + 100 + 200 + 400 = $750 at risk
- BTC 5-min outcomes are roughly 50/50 — 4 consecutive same-direction moves happen ~6% of the time
- Ruin probability is unacceptably high
- Martingale only works with infinite bankroll (you don't have one)

---

## SCALPER-TURBO

**Concept**: Maximize throughput — fast cycles, low merge targets, rapid reentry.

**Parameters**:
- Merge target: 5 pairs (instead of 10-20)
- Reentry delay: 0.5s after merge
- Buffer time: 30s (aggressive — close to market end)
- Tight offsets: -1¢, -2¢

**Paper Trading Result**: Never fully tested

**Live Result**: Never deployed

**Concerns**: Tight offsets mean constant adverse selection risk. The -1¢ offset is basically market-taking with extra steps.

---

## SCALPER-REQUOTE

**Concept**: Adaptively reprice orders every 5 seconds based on current market conditions. If the market moves, move your orders.

**Parameters**:
- Requote interval: 5s
- Price adjustment: track best bid/ask and maintain constant offset
- Cancel-and-replace pattern

**Paper Trading Result**: Never fully tested

**Live Result**: Never deployed

**Concerns**:
- Cancel-and-replace creates gaps where you have no orders (miss fills)
- High API call volume (cancel + place every 5s × multiple orders)
- Requoting into a moving market can chase price

---

## PAIR-HUNTER

**Concept**: Aggressively pursue completed pairs. Place orders on both sides with tight spreads, prioritize pairing over directional exposure.

**Parameters**:
- Aggressive offsets: -1¢, -2¢ on both sides
- Immediate merge when pair completes
- No buffer time — trade until market close

**Gamma-Verified Result**: **-$508**

**Breakdown**:
- 74% of filled tokens were **unmatched** (only one side filled)
- Merge edge on completed pairs was positive
- Settle losses on 74% unmatched inventory destroyed everything

**Lesson**: You can't force pairing. The market decides which side gets filled.

---

## Signal-Based (v3 Engine)

**Concept**: Systematic approach — test 18 different entry signals × 6 ladder configurations = 108 combinations. Use historical data to find profitable combos.

**Signals Tested (18)**:
- OFI-based (3 variants): raw OFI, smoothed OFI, OFI acceleration
- Volume-based — H2 family (4 variants): volume surge, VPIN, volume ratio, volume momentum
- Price-based (3 variants): momentum, mean reversion, range breakout
- Book-based (4 variants): book pressure, spread change, depth imbalance, queue position
- Composite (4 variants): various combinations of above

**Ladder Configurations (6)**:
- Conservative: -3,-4,-5¢ offsets
- Moderate: -2,-3,-4¢
- Aggressive: -1,-2,-3¢
- Asymmetric: -1¢ favored side, -4¢ unfavored
- Single: best offset only
- Dynamic: offset based on sigma

**Results**:
- **Only 16 out of 102 evaluated combos showed positive PnL**
- Overall Kelly criterion: **-2.8%** (negative = don't bet)
- Volume-based signals (H2 family) performed best but still not reliably profitable
- No single signal + ladder combo was consistently profitable across different time periods

**Analysis**:
The v3 engine was the most rigorous approach. Its conclusion:
- The edge (merge profit from completed pairs) is real but thin
- The risk (settle loss from unmatched inventory) is structural
- No signal quality improvement can fully solve the unmatched inventory problem
- The market is efficient enough that informed traders (with better signals/speed) take the other side

---

## Key Lessons

### 1. Paper Trading Is a Lie

Paper fill simulation (`if ask ≤ bid → fill`) is dramatically more optimistic than real execution. In reality:
- Your orders sit in a queue behind other market makers
- Fills happen when someone aggresses into your price — which often means the market is moving against you
- Paper trading doesn't model queue position, partial fills, or adverse selection

### 2. Outcome Verification Bugs Are Expensive

We lost real money because our outcome verification was broken:
- Checking the Gamma API too early → prices not yet resolved → wrong outcome detected
- Using mid-market prices as a proxy for outcomes → unreliable
- **Fix**: ALWAYS check `umaResolutionStatus == "resolved"` FIRST, then read `outcomePrices`

### 3. Unmatched Inventory Is the #1 Killer

More important than entry signal quality. Even a perfect signal can't prevent asymmetric fills:
- When BTC moves, one side of the book gets swept
- Your unfilled orders on the other side become stale
- You're left holding tokens on one side, exposed to the outcome

### 4. Merge Edge Is Real But Uncapturable (So Far)

The math works: if `up_cost + dn_cost < 1.0`, merging profits. But:
- Getting both sides filled at good prices simultaneously is the hard problem
- The market naturally resists this (efficient pricing)
- Anyone who solves this reliably has a printing press

### 5. Verify Everything

Dashboard numbers mean **NOTHING** until verified against ground truth:
- Cross-check PnL against actual USDC balance changes
- Verify outcomes against Gamma API (not engine predictions)
- Verify fills against on-chain data when possible

### 6. Timing Matters More Than Signal Quality

In 5-minute markets:
- Entering in the first 30 seconds is critical
- Late entry (>60s) = adverse selection (the market already moved)
- The last 30 seconds are the most dangerous (prices converge to outcome)

---

*See also: [Metrics & Calculations](metrics-calculations.md) · [Architecture Patterns](architecture-patterns.md) · [Pitfalls](pitfalls.md)*
