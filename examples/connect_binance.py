"""
Connect to Binance Spot + Futures WebSocket streams.

Tracks BTC/USDT trades and best bid/ask from both spot and futures.

Usage:
    python connect_binance.py
"""

import asyncio
import json
import websockets

# === Stream URLs ===
SPOT_URL = "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/btcusdt@bookTicker"
FUTURES_URL = "wss://fstream.binance.com/stream?streams=btcusdt@aggTrade/btcusdt@bookTicker"


class BinanceTracker:
    """Track BTC price from Binance streams."""

    def __init__(self):
        self.spot_price = None
        self.spot_bid = None
        self.spot_ask = None
        self.futures_price = None
        self.futures_bid = None
        self.futures_ask = None
        self.trade_count = 0

    def handle_spot_trade(self, data: dict):
        self.spot_price = float(data["p"])
        self.trade_count += 1

    def handle_spot_book(self, data: dict):
        self.spot_bid = float(data["b"])
        self.spot_ask = float(data["a"])

    def handle_futures_trade(self, data: dict):
        self.futures_price = float(data["p"])

    def handle_futures_book(self, data: dict):
        self.futures_bid = float(data["b"])
        self.futures_ask = float(data["a"])

    def display(self):
        print(
            f"SPOT: {self.spot_bid}/{self.spot_ask} (last: {self.spot_price})  "
            f"FUT: {self.futures_bid}/{self.futures_ask} (last: {self.futures_price})  "
            f"trades: {self.trade_count}"
        )


tracker = BinanceTracker()


async def handle_stream(url: str, label: str):
    """Connect to a Binance combined stream with reconnection."""
    backoff = 1

    while True:
        try:
            async with websockets.connect(
                url, ping_interval=60, ping_timeout=30
            ) as ws:
                backoff = 1
                print(f"Connected to Binance {label}")

                async for raw in ws:
                    msg = json.loads(raw)
                    stream = msg.get("stream", "")
                    data = msg.get("data", {})

                    if stream == "btcusdt@trade":
                        tracker.handle_spot_trade(data)
                    elif stream == "btcusdt@bookTicker" and "spot" in label.lower():
                        tracker.handle_spot_book(data)
                    elif stream == "btcusdt@aggTrade":
                        tracker.handle_futures_trade(data)
                    elif stream == "btcusdt@bookTicker":
                        tracker.handle_futures_book(data)

                    # Display every 100 events to avoid flooding
                    if tracker.trade_count % 100 == 0:
                        tracker.display()

        except (websockets.ConnectionClosed, ConnectionError, OSError) as e:
            print(f"Binance {label} disconnected: {e}. Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


async def main():
    """Run both spot and futures streams concurrently."""
    await asyncio.gather(
        handle_stream(SPOT_URL, "Spot"),
        handle_stream(FUTURES_URL, "Futures"),
    )


if __name__ == "__main__":
    asyncio.run(main())
