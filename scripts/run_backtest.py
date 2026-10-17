#!/usr/bin/env python3
"""
Run a full backtest of the SMA Crossover strategy.
Usage:
    python scripts/run_backtest.py
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest import Backtester
from src.data import fetch_ohlcv
from src.strategy import SMACrossoverStrategy
from src.utils import load_config, setup_logging

logger = setup_logging(level="INFO")


def main():
    config = load_config(ROOT / "config" / "config.yaml")

    # Strategy parameters
    strat_cfg = config["strategy"]
    bt_cfg = config["backtest"]

    strategy = SMACrossoverStrategy(
        short_window=strat_cfg["short_window"],
        long_window=strat_cfg["long_window"],
    )

    # Data
    data = fetch_ohlcv(
        symbol=strat_cfg["symbol"],
        start=bt_cfg["start_date"],
        end=bt_cfg.get("end_date"),
    )

    # Backtest
    backtester = Backtester(
        strategy=strategy,
        initial_capital=bt_cfg["initial_capital"],
        commission=bt_cfg["commission"],
        slippage=bt_cfg["slippage"],
        quantity=strat_cfg["quantity"],
    )

    result = backtester.run(data)
    backtester.print_metrics(result)
    backtester.plot(result, title=f"{strat_cfg['symbol']} – {strategy.name}")

    # Optionally save equity curve
    output_path = ROOT / "data" / "equity_curve.csv"
    result.equity_curve.to_csv(output_path)
    logger.info(f"Equity curve saved to {output_path}")


if __name__ == "__main__":
    main()
