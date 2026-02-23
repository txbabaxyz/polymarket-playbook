# Polymarket On-Chain Operations

> CTF merge, redeem, allowances, and USDC balance on Polygon.

## Table of Contents

- [Overview](#overview)
- [CTF Merge](#ctf-merge)
- [Redeem](#redeem)
- [Allowances](#allowances)
- [USDC Balance](#usdc-balance)
- [Proxy Wallets vs EOA](#proxy-wallets-vs-eoa)

---

## Overview

Polymarket runs on **Polygon PoS**. Outcome tokens follow the **Conditional Token Framework (CTF)** standard. All on-chain operations interact with CTF contracts on Polygon.

Key contracts (verify on Polygonscan — addresses may update):
- **CTF Exchange**: The main trading contract
- **USDC**: Standard ERC-20 on Polygon (6 decimals)
- **Conditional Tokens**: ERC-1155 tokens representing outcomes

---

## CTF Merge

> **The core of market-making profit.**

Merging combines equal quantities of ALL outcome tokens back into the collateral (USDC).

For a binary market:
```
1 UP token + 1 DN token → $1.00 USDC
```

### Why Merge?

If you bought:
- 100 UP tokens at $0.47 each = $47.00
- 100 DN tokens at $0.50 each = $50.00
- Total cost: $97.00

Merging 100 pairs:
- 100 × $1.00 = $100.00
- **Profit: $3.00** (regardless of which outcome wins)

### How to Merge

```python
from py_clob_client.client import ClobClient

client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key="YOUR_PRIVATE_KEY",
    signature_type=0,
)

# Merge paired tokens
# The client handles the on-chain transaction
result = client.merge(
    condition_id="CONDITION_ID_HERE",
    amount=100,  # Number of pairs to merge
)
print(f"Merge tx: {result}")
```

### Merge Economics

| Scenario | UP Cost | DN Cost | Total | Merge Return | Profit |
|----------|---------|---------|-------|-------------|--------|
| Tight spread | $0.49 | $0.50 | $0.99 | $1.00 | $0.01/pair |
| Normal spread | $0.47 | $0.50 | $0.97 | $1.00 | $0.03/pair |
| Wide spread | $0.45 | $0.50 | $0.95 | $1.00 | $0.05/pair |

The merge edge is **sigma minus 1.0** when buying at the ask: `merge_edge = 1.0 - (up_ask + dn_ask)` … wait, that's negative. Actually the merge edge comes from buying at bid-side or getting filled on resting orders below the ask.

**Real merge edge = 1.0 - (cost_per_up + cost_per_dn)**

---

## Redeem

After a market resolves, winning tokens can be redeemed for $1.00 each.

```python
# Redeem winning tokens after resolution
result = client.redeem(
    condition_id="CONDITION_ID_HERE",
)
print(f"Redeem tx: {result}")
```

### Important Notes

- Only the winning token is redeemable
- Losing tokens become worthless (value = $0.00)
- Redeem is an on-chain transaction (gas costs apply, though minimal on Polygon)
- You must wait until `umaResolutionStatus == "resolved"` before redeeming

---

## Allowances

Before trading, you must approve the CTF Exchange contract to spend your USDC.

```python
# Set USDC allowance for the exchange
# This is typically done once with a large approval
result = client.set_allowance()
print(f"Allowance tx: {result}")
```

### Check Existing Allowance

If your orders are being rejected with allowance errors, verify:
1. USDC approval is set for the CTF Exchange contract
2. The approval amount is sufficient for your order size
3. You're using the correct wallet (EOA vs proxy)

---

## USDC Balance

Check your USDC balance on Polygon:

```python
import httpx

# Via Polygon RPC
POLYGON_RPC = "https://polygon-rpc.com"
USDC_ADDRESS = "0xUSDC_CONTRACT_ON_POLYGON"  # Look up on Polygonscan

# Or use the py-clob-client
balance = client.get_balance()
print(f"USDC Balance: {balance}")
```

### Balance Considerations

- USDC on Polygon uses **6 decimals** (1 USDC = 1,000,000 units)
- Keep some MATIC for gas (minimal, ~0.01 MATIC per transaction)
- Open orders **lock** your USDC — available balance = total - locked

---

## Proxy Wallets vs EOA

### EOA (Externally Owned Account)

- Your direct Ethereum wallet (MetaMask, etc.)
- Use `signature_type=0` in orders
- You control the private key directly
- Simpler setup

### Proxy Wallet (Gnosis Safe)

- Created by Polymarket when you deposit via their UI
- Use `signature_type=2` in orders
- The proxy wallet holds your funds
- Your EOA is the owner/signer

### How to Know Which You're Using

```python
# If you deposited via Polymarket UI → likely proxy wallet
client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key="YOUR_PRIVATE_KEY",
    signature_type=2,  # Proxy
)

# If you sent USDC directly to your EOA on Polygon → EOA
client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key="YOUR_PRIVATE_KEY",
    signature_type=0,  # EOA
)
```

### Common Issue

Using the wrong `signature_type` causes orders to be rejected silently or with cryptic errors. If your orders aren't going through, try switching between 0 and 2.

---

*See also: [CLOB API](polymarket-api.md) · [Market Structure](polymarket-markets.md) · [Metrics](metrics-calculations.md)*
