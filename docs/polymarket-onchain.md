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

### Core Contract Addresses (Polygon Mainnet, Chain ID 137)

| Contract | Address |
|----------|---------|
| **CTF Exchange** | `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E` |
| **Neg Risk CTF Exchange** | `0xC5d563A36AE78145C45a50134d48A1215220f80a` |
| **Neg Risk Adapter** | `0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296` |
| **Conditional Tokens (CTF)** | `0x4D97DCd97eC945f40cF65F87097ACe5EA0476045` |
| **USDC.e (Bridged USDC)** | `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` |
| **Gnosis Safe Factory** | `0xaacfeea03eb1561c4e67d661e40682bd20e3541b` |
| **Polymarket Proxy Factory** | `0xaB45c5A4B0c941a2F231C04C3f49182e1A254052` |
| **UMA Adapter v2** | `0x6A9D222616C90FcA5754cd1333cFD9b7fb6a4F74` |
| **Uniswap v3 USDC.e/USDC** | `0xd36ec33c8bed5a9f7b6630855f1533455b98a418` |

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

## Negative Risk Markets

Multi-outcome events use the **Neg Risk Adapter** for capital-efficient trading:

- A **No share** in any market can be converted into **1 Yes share in every other market** in the event
- This conversion is atomic through the Neg Risk Adapter contract
- Orders on neg risk markets must specify `negRisk: true` / `neg_risk: True`

### Identifying Neg Risk

The Gamma API includes `negRisk` boolean on events/markets. For **augmented neg risk** (new outcomes can be added):
```json
{"enableNegRisk": true, "negRiskAugmented": true}
```

**Rule**: Only trade named outcomes in augmented neg risk — ignore placeholders until clarified.

---

## Gasless Transactions (Builder Program)

Through the **Relayer Client**, Builder Program members can sponsor gas for users:

- Wallet deployment, token approvals, CTF operations (split/merge/redeem), transfers
- Users only need USDC.e — no POL required
- Relayer endpoint: `https://relayer-v2.polymarket.com/`
- Requires Builder API credentials for authentication

---

## Subgraph (On-Chain GraphQL)

Polymarket subgraphs (hosted by Goldsky) provide indexed on-chain data:

| Subgraph | Description |
|----------|-------------|
| Positions | User token balances |
| Orders | Order book and trade events |
| Activity | Splits, merges, redemptions, neg risk conversions |
| Open Interest | Per-market and global OI |
| PNL | User position P&L |

Base endpoint: `https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/`

Source: [github.com/Polymarket/polymarket-subgraph](https://github.com/Polymarket/polymarket-subgraph)

---

*See also: [CLOB API](polymarket-api.md) · [Market Structure](polymarket-markets.md) · [Metrics](metrics-calculations.md)*
