# 🎯 Polymarket Playbook

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Polymarket](https://img.shields.io/badge/Polymarket-CLOB%20API-purple)](https://docs.polymarket.com)
[![Binance](https://img.shields.io/badge/Binance-WebSocket-orange)](https://binance-docs.github.io/apidocs/)

> **Everything an AI agent or developer needs to instantly start building trading products on Polymarket + Binance.**

A battle-tested knowledge base distilled from months of building, testing, and (mostly losing money on) automated trading systems for Polymarket's binary options markets — with Binance price feeds as the signal source.

---

## 📖 Table of Contents

- [What Is This?](#what-is-this)
- [Who Is This For?](#who-is-this-for)
- [Documentation](#documentation)
- [Examples](#examples)
- [Key Concepts](#key-concepts)
- [Hard Truths](#hard-truths)
- [Getting Started](#getting-started)
- [License](#license)

---

## What Is This?

This repository is a **comprehensive reference** for building on:

1. **Polymarket CLOB** — a prediction market exchange on Polygon where you trade binary outcome tokens (e.g., "Will BTC go up in the next 5 minutes?")
2. **Binance WebSocket feeds** — real-time cryptocurrency price data used as signals for trading decisions

It covers APIs, WebSockets, market structure, order management, on-chain operations, trading metrics, architecture patterns, and — critically — **every strategy we tested and why none of them worked profitably in production**.

## Who Is This For?

- **Developers** building trading bots or analytics tools on Polymarket
- **AI agents** that need structured knowledge about Polymarket's API surface
- **Researchers** studying prediction market microstructure
- **Anyone** who wants to save months of painful discovery

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Polymarket CLOB API](docs/polymarket-api.md) | REST API endpoints, authentication, order types, rate limits |
| [Polymarket WebSocket](docs/polymarket-websocket.md) | Market & User WebSocket channels, real-time data |
| [Market Structure & Resolution](docs/polymarket-markets.md) | Market anatomy, lifecycle, outcome verification via Gamma API |
| [Order Management](docs/polymarket-orders.md) | Placing, tracking, cancelling orders; batch operations |
| [On-Chain Operations](docs/polymarket-onchain.md) | CTF merge, redeem, allowances, USDC on Polygon |
| [Binance WebSocket](docs/binance-websocket.md) | Spot & futures streams, trade/bookTicker feeds |
| [Metrics & Calculations](docs/metrics-calculations.md) | Sigma, RV, OFI, VPIN, PnL math, Kelly criterion |
| [Strategies Tested](docs/strategies-tested.md) | Every strategy we tried — honest results (spoiler: all unprofitable) |
| [Architecture Patterns](docs/architecture-patterns.md) | Engine design, watchdog, paper trading, JSONL logging |
| [Pitfalls & Lessons](docs/pitfalls.md) | Critical mistakes and hard-won lessons |

## 💻 Examples

| Example | Description |
|---------|-------------|
| [connect_clob_ws.py](examples/connect_clob_ws.py) | Connect to Polymarket market WebSocket |
| [connect_user_ws.py](examples/connect_user_ws.py) | Connect to Polymarket user WebSocket |
| [connect_binance.py](examples/connect_binance.py) | Connect to Binance spot + futures streams |
| [place_order.py](examples/place_order.py) | Place a GTC order via py-clob-client |
| [batch_orders.py](examples/batch_orders.py) | Batch order placement (up to 100 orders) |
| [check_outcome.py](examples/check_outcome.py) | Verify market outcome via Gamma API |
| [calculate_metrics.py](examples/calculate_metrics.py) | Calculate sigma, RV, OFI from WebSocket data |

## 🔑 Key Concepts

### The Polymarket Binary Options Model

Polymarket offers binary outcome markets. For BTC 5-minute markets:
- Each market has two tokens: **UP** and **DN**
- Tokens trade between $0.00 and $1.00
- After resolution, the winning token = $1.00, losing token = $0.00
- You can **merge** one UP + one DN token back into $1.00 at any time

### The Merge Edge

If you buy 1 UP token at $0.47 and 1 DN token at $0.50, your total cost is $0.97. Merging them gives you $1.00 — a $0.03 profit regardless of outcome. This is the core of market-making on Polymarket.

### The Catch

Getting both sides filled at favorable prices simultaneously is extremely difficult. You almost always end up with **unmatched inventory** — tokens on one side that are exposed to the outcome. This settle risk typically destroys the merge edge.

## ⚠️ Hard Truths

> **🔴 None of the strategies documented here are profitable in production.**

This is not a "copy and profit" repository. It's a knowledge base that documents:
- What the APIs look like and how to use them correctly
- What strategies were attempted and why they failed
- What the real challenges are (not the obvious ones)

The merge edge is real (3-7¢ per pair). Capturing it without settle risk is the unsolved problem.

## 🚀 Getting Started

```bash
# Install the Polymarket Python client
pip install py-clob-client

# Install WebSocket library
pip install websockets

# Install HTTP client
pip install httpx

# Set up your environment
export POLY_API_KEY="YOUR_API_KEY"
export POLY_API_SECRET="YOUR_API_SECRET"
export POLY_PASSPHRASE="YOUR_PASSPHRASE"
export POLY_PRIVATE_KEY="YOUR_PRIVATE_KEY"
```

Then start with:
1. Read [Polymarket API docs](docs/polymarket-api.md) to understand the REST surface
2. Read [Market Structure](docs/polymarket-markets.md) to understand what you're trading
3. Run [connect_clob_ws.py](examples/connect_clob_ws.py) to see live market data
4. Read [Pitfalls](docs/pitfalls.md) before writing any trading logic

## License

[MIT](LICENSE)
