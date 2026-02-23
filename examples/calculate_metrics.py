"""
Calculate trading metrics from WebSocket data.

Demonstrates sigma, realized volatility, OFI, and VWAP calculations.

Usage:
    python calculate_metrics.py
"""

import asyncio
import json
import math
import time
from collections import deque
import websockets

# === Configuration ===
BINANCE_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"
POLY_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

# Metrics window (seconds)
WINDOW = 30.0


class MetricsCalculator:
    """Calculate real-time trading metrics."""

    def __init__(self, window: float = 30.0):
        self.window = window
        self.trades = deque()       # (timestamp, price, quantity, is_buyer_maker)
        self.high = None
        self.low = None
        self.up_ask = None
        self.dn_ask = None

    # --- Binance Trade Handling ---

    def add_trade(self, price: float, qty: float, is_buyer_maker: bool, ts: float):
        """Add a Binance trade to the rolling window."""
        self.trades.append((ts, price, qty, is_buyer_maker))

        # Track high/low
        if self.high is None or price > self.high:
            self.high = price
        if self.low is None or price < self.low:
            self.low = price

        # Prune old trades
        cutoff = ts - self.window
        while self.trades and self.trades[0][0] < cutoff:
            self.trades.popleft()

    # --- Sigma (from Polymarket) ---

    def update_poly_ask(self, token_id: str, price: float, is_up: bool):
        """Update Polymarket ask prices."""
        if is_up:
            self.up_ask = price
        else:
            self.dn_ask = price

    def sigma(self) -> float | None:
        """σ = up_ask + dn_ask. Perfect = 1.00."""
        if self.up_ask is None or self.dn_ask is None:
            return None
        return self.up_ask + self.dn_ask

    # --- VWAP ---

    def vwap(self) -> float | None:
        """Volume-Weighted Average Price over the window."""
        if not self.trades:
            return None
        total_vol = sum(qty for _, _, qty, _ in self.trades)
        if total_vol == 0:
            return None
        return sum(p * q for _, p, q, _ in self.trades) / total_vol

    # --- Order Flow Imbalance ---

    def ofi(self) -> float:
        """
        Order Flow Imbalance.
        > 0 = buying pressure (bullish)
        < 0 = selling pressure (bearish)
        Range: -1.0 to 1.0
        """
        if not self.trades:
            return 0.0

        buy_vol = sum(q for _, _, q, m in self.trades if not m)
        sell_vol = sum(q for _, _, q, m in self.trades if m)
        total = buy_vol + sell_vol

        if total == 0:
            return 0.0
        return (buy_vol - sell_vol) / total

    # --- Realized Volatility (Parkinson) ---

    def realized_volatility(self) -> float | None:
        """
        Parkinson realized volatility from high/low in the window.
        Single-period estimate.
        """
        if self.high is None or self.low is None or self.low == 0:
            return None
        return math.log(self.high / self.low) / (2 * math.sqrt(math.log(2)))

    # --- Display ---

    def display(self):
        vwap = self.vwap()
        ofi = self.ofi()
        rv = self.realized_volatility()
        sigma = self.sigma()

        parts = [
            f"VWAP: ${vwap:,.2f}" if vwap else "VWAP: --",
            f"OFI: {ofi:+.3f}",
            f"RV: {rv:.6f}" if rv else "RV: --",
            f"σ: {sigma:.4f}" if sigma else "σ: --",
            f"Trades: {len(self.trades)}",
        ]
        print("  |  ".join(parts))


async def binance_feed(calc: MetricsCalculator):
    """Stream Binance trades into the calculator."""
    backoff = 1
    while True:
        try:
            async with websockets.connect(BINANCE_URL, ping_interval=60) as ws:
                backoff = 1
                print("Connected to Binance trade stream")
                async for raw in ws:
                    msg = json.loads(raw)
                    calc.add_trade(
                        price=float(msg["p"]),
                        qty=float(msg["q"]),
                        is_buyer_maker=msg["m"],
                        ts=msg["T"] / 1000.0,
                    )
        except Exception as e:
            print(f"Binance error: {e}, reconnecting in {backoff}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


async def display_loop(calc: MetricsCalculator):
    """Print metrics every 5 seconds."""
    while True:
        await asyncio.sleep(5)
        calc.display()


async def main():
    calc = MetricsCalculator(window=WINDOW)
    print(f"Calculating metrics over {WINDOW}s rolling window\n")

    await asyncio.gather(
        binance_feed(calc),
        display_loop(calc),
    )


if __name__ == "__main__":
    asyncio.run(main())
