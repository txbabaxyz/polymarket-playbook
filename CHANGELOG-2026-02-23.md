# Changelog — 2026-02-23

Comprehensive update of all Polymarket Playbook documentation based on official Polymarket API docs (https://docs.polymarket.com) and recent analysis data.

## Files Updated

### `docs/polymarket-api.md` — Major Rewrite
- **Added**: Three-API architecture (Gamma, Data, CLOB) with all base URLs
- **Added**: Complete Gamma API endpoint table (markets, events, tags, series, comments, profiles, sports, search, prices history)
- **Added**: Complete Data API endpoint table (positions, closed positions, trades, activity, leaderboard, open interest, volume, accounting snapshots, builder endpoints)
- **Added**: Complete CLOB market data endpoints (book, books, price, prices, midpoint, midpoints, spread, spreads, last-trade-price, tick-size, fee-rate, prices-history, server time)
- **Added**: Complete CLOB trading endpoints (heartbeat, order-scoring, cancel-all, cancel-market-orders)
- **Added**: FAK (Fill And Kill) order type, Post-Only orders
- **Added**: Signature type 1 (POLY_PROXY for Magic Link users)
- **Added**: Bridge API endpoints (deposit-addresses, withdrawal-addresses, quote, supported-assets, transaction-status)
- **Updated**: Batch order limit corrected to 15 (was 100)
- **Updated**: Rate limits with exact numbers from official docs (per-API breakdowns, burst vs sustained for trading)
- **Updated**: Fee structure with formula, fee tables, maker rebate percentages
- **Updated**: Error codes with complete list from official docs (global, orderbook, pricing, orders, matching engine, cancellation errors)
- **Added**: SDK section with all three languages (TypeScript, Python, Rust) + Builder SDKs + Relayer SDKs
- **Updated**: Authentication section with correct L1 vs L2 header details

### `docs/polymarket-websocket.md` — Significant Update
- **Added**: Sports WebSocket channel (`wss://sports-api.polymarket.com/ws`)
- **Added**: RTDS (Real-Time Data Socket) channel (`wss://ws-live-data.polymarket.com`)
- **Fixed**: Subscription field name corrected to `assets_ids` (plural)
- **Added**: `custom_feature_enabled` flag for best_bid_ask, new_market, market_resolved events
- **Added**: Dynamic subscription/unsubscription without reconnecting
- **Added**: All 7 market channel message types with examples (book, price_change, tick_size_change, last_trade_price, best_bid_ask, new_market, market_resolved)
- **Added**: User channel auth format with apiKey/secret/passphrase object
- **Added**: Trade status flow diagram (MATCHED → MINED → CONFIRMED / RETRYING → FAILED)
- **Updated**: Heartbeat details (PING/PONG for market/user, ping/pong for sports)

### `docs/polymarket-markets.md` — Extended
- **Updated**: UMA resolution with full lifecycle (proposal, 2hr challenge, dispute, DVM vote)
- **Added**: UMA Adapter contract addresses (v1, v2, v3)
- **Added**: Resolution timeline table (undisputed ~2h, 1 dispute ~4d, 2 disputes ~6d)
- **Added**: Clarifications mechanism (bulletin board, onchain context updates)
- **Added**: Sports markets section (auto-cancel at game start, 3s matching delay)
- **Added**: Holding Rewards section (4.00% annualized, hourly sampling, daily distribution)

### `docs/polymarket-onchain.md` — Extended
- **Updated**: Complete contract address table with all verified addresses from official docs
- **Added**: Neg Risk CTF Exchange, Neg Risk Adapter, Gnosis Safe Factory, Proxy Factory, Uniswap pool addresses
- **Added**: Negative Risk Markets section (conversion mechanics, identifying neg risk, augmented neg risk)
- **Added**: Gasless Transactions section (Builder Program relayer, covered operations)
- **Added**: Subgraph section (5 subgraphs on Goldsky: Positions, Orders, Activity, Open Interest, PNL)

### `docs/polymarket-orders.md` — Corrected
- **Fixed**: Batch order limit corrected from 100 to 15

### `docs/polymarket-api.md` — See Major Rewrite above

### `docs/pitfalls.md` — Extended
- **Added**: Geoblock check endpoint (`GET https://polymarket.com/api/geoblock`)
- **Added**: Complete blocked countries list (30+ countries, 4 close-only, blocked regions)
- **Added**: Pitfall #9 — Matching Engine Restarts (HTTP 425 handling)
- **Added**: Pitfall #10 — Fee-Enabled Markets (feeRateBps requirement)

### `docs/strategies-tested.md` — Extended with Analysis Data
- **Added**: Martingale Deep-Dive section with full statistical analysis
- **Added**: Dataset table (BTC 2014 markets, XRP 1431, ETH 1432, SOL 1432)
- **Added**: BTC 7-day streak distribution (52.1% UP, max streak 7)
- **Added**: Runs Test findings (all p > 0.05, outcomes indistinguishable from random)
- **Added**: Martingale N=2 through N=8 analysis
- **Added**: Binance indicator enhancement results table (all 4 assets)
- **Added**: Binance vs Polymarket outcome comparison (97-98% match, Chainlink differences)

### `docs/metrics-calculations.md` — Extended with Indicator Analysis
- **Added**: Complete Binance Indicator Analysis section
- **Added**: Table of all 14 indicators tested with descriptions
- **Added**: Per-asset best indicator results (all non-significant, AUC 0.47-0.55)
- **Added**: Conclusion: zero statistically significant predictive power
- **Added**: Basic vs Enhanced backtest comparison reference

## Sources

- Official Polymarket docs: https://docs.polymarket.com/llms.txt (full index)
- 90+ pages fetched from docs.polymarket.com covering all sections
- `/tmp/indicator-analysis.md` — 14-indicator analysis results
- `/root/.openclaw/workspace/market-analysis-results.md` — streak analysis
