#!/usr/bin/env python3
"""
Run the SMA Crossover strategy in Interactive Brokers paper trading.

Prerequisites:
1. TWS or IB Gateway running
2. Logged into a PAPER trading account
3. API enabled (port 7497 by default)

Usage:
    python scripts/run_paper_trading.py
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.paper_trader import IBPaperTrader
from src.strategy import SMACrossoverStrategy
from src.utils import load_config, setup_logging

logger = setup_logging(level="INFO", log_file="logs/paper_trading.log")


def main():
    config = load_config(ROOT / "config" / "config.yaml")

    strat_cfg = config["strategy"]
    ib_cfg = config["ibkr"]

    strategy = SMACrossoverStrategy(
        short_window=strat_cfg["short_window"],
        long_window=strat_cfg["long_window"],
    )

    trader = IBPaperTrader(
        strategy=strategy,
        symbol=strat_cfg["symbol"],
        quantity=strat_cfg["quantity"],
        host=ib_cfg["host"],
        port=ib_cfg["port"],
        client_id=ib_cfg["client_id"],
    )

    try:
        trader.connect_and_start()

        # Request current positions
        trader.reqPositions()

        logger.info("Starting paper trading loop (Ctrl+C to stop)...")
        logger.info("Evaluating signal once, then you can schedule this script daily.")

        # For a simple demo we evaluate once.
        # In production you would schedule this (cron / task scheduler)
        # to run after market close each day.
        trader.evaluate_and_trade()

        # Keep the connection alive for a while to receive order status
        logger.info("Waiting 30 seconds for order updates...")
        time.sleep(30)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    finally:
        trader.disconnect_gracefully()


if __name__ == "__main__":
    main()
