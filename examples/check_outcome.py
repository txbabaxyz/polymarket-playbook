"""
Verify market outcome via Gamma API.

THE ONLY correct method for determining market resolution.

Usage:
    python check_outcome.py btc-updown-5m-1700000000
"""

import sys
import time
import httpx

GAMMA_API = "https://gamma-api.polymarket.com/markets"


def check_outcome(slug: str, max_retries: int = 20, retry_interval: float = 5.0) -> str:
    """
    Check market outcome via Gamma API.

    CRITICAL RULES:
    1. ALWAYS check umaResolutionStatus == "resolved" FIRST
    2. The winner has outcomePrices == "1"
    3. NEVER guess from mid-prices
    4. Retry if not yet resolved

    Returns:
        Winning outcome name (e.g., "Up" or "Down")

    Raises:
        TimeoutError if not resolved within retries
    """
    url = f"{GAMMA_API}?slug={slug}"

    for attempt in range(1, max_retries + 1):
        resp = httpx.get(url, timeout=10)
        data = resp.json()

        if not data:
            print(f"  Attempt {attempt}: No market found for slug '{slug}'")
            time.sleep(retry_interval)
            continue

        market = data[0]
        resolution_status = market.get("umaResolutionStatus")

        # STEP 1: Check resolution status
        if resolution_status != "resolved":
            print(f"  Attempt {attempt}: Status = '{resolution_status}' (not resolved yet)")
            time.sleep(retry_interval)
            continue

        # STEP 2: Parse outcomes
        outcomes = market.get("outcomes", [])
        prices = market.get("outcomePrices", [])

        print(f"  Attempt {attempt}: RESOLVED!")
        print(f"  Outcomes: {outcomes}")
        print(f"  Prices:   {prices}")

        # STEP 3: Find the winner (price == "1")
        for outcome, price in zip(outcomes, prices):
            if price == "1":
                print(f"  🏆 Winner: {outcome}")
                return outcome

        raise ValueError(f"No winning outcome found in prices: {prices}")

    raise TimeoutError(f"Market '{slug}' not resolved after {max_retries} attempts")


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_outcome.py <market-slug>")
        print("Example: python check_outcome.py btc-updown-5m-1700000000")
        sys.exit(1)

    slug = sys.argv[1]
    print(f"Checking outcome for: {slug}")

    try:
        winner = check_outcome(slug)
        print(f"\n✅ Market resolved: {winner} wins!")
    except TimeoutError as e:
        print(f"\n⏳ {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
