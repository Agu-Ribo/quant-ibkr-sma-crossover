"""
Simple but robust backtesting engine for the SMA Crossover strategy.
"""

from dataclasses import dataclass
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.strategy import SMACrossoverStrategy
from src.utils import setup_logging

logger = setup_logging()


@dataclass
class BacktestResult:
    """Container for backtest performance metrics and equity curve."""
    equity_curve: pd.Series
    returns: pd.Series
    trades: pd.DataFrame
    metrics: Dict[str, float]


class Backtester:
    """
    Event-driven style backtester (simplified).

    Assumptions:
    - Signals are executed at the next bar's open (or close for simplicity).
    - Fixed position size (number of shares).
    - Commission and slippage are applied.
    """

    def __init__(
        self,
        strategy: SMACrossoverStrategy,
        initial_capital: float = 100_000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        quantity: int = 100,
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.quantity = quantity

    def run(self, data: pd.DataFrame) -> BacktestResult:
        """
        Execute the backtest.

        Parameters
        ----------
        data : pd.DataFrame
            Must contain a 'Close' column and a DatetimeIndex.
        """
        logger.info("Running backtest...")

        signals = self.strategy.generate_signals(data)
        signals = signals.dropna(subset=[f"SMA_{self.strategy.long_window}"])

        # We execute on the bar AFTER the signal
        signals["exec_price"] = signals["Close"].shift(-1)  # next bar close (simplification)
        signals = signals.dropna(subset=["exec_price"])

        cash = self.initial_capital
        position = 0  # number of shares
        equity = []
        trade_log = []

        for i, (ts, row) in enumerate(signals.iterrows()):
            signal = row["Signal"]  # 1 = BUY, -1 = SELL, 0 = HOLD
            price = row["exec_price"]

            # Apply slippage
            if signal == 1:  # buy
                price *= (1 + self.slippage)
            elif signal == -1:  # sell
                price *= (1 - self.slippage)

            # Execute
            if signal == 1 and position == 0:
                cost = self.quantity * price
                commission_cost = cost * self.commission
                if cash >= cost + commission_cost:
                    cash -= cost + commission_cost
                    position = self.quantity
                    trade_log.append(
                        {
                            "timestamp": ts,
                            "action": "BUY",
                            "price": price,
                            "quantity": self.quantity,
                            "commission": commission_cost,
                        }
                    )

            elif signal == -1 and position > 0:
                proceeds = position * price
                commission_cost = proceeds * self.commission
                cash += proceeds - commission_cost
                trade_log.append(
                    {
                        "timestamp": ts,
                        "action": "SELL",
                        "price": price,
                        "quantity": position,
                        "commission": commission_cost,
                    }
                )
                position = 0

            # Mark-to-market equity
            market_value = position * row["Close"]
            total_equity = cash + market_value
            equity.append({"timestamp": ts, "equity": total_equity})

        equity_df = pd.DataFrame(equity).set_index("timestamp")
        equity_curve = equity_df["equity"]
        returns = equity_curve.pct_change().fillna(0)

        trades = pd.DataFrame(trade_log)
        metrics = self._calculate_metrics(equity_curve, returns, trades)

        logger.info("Backtest finished")
        return BacktestResult(
            equity_curve=equity_curve,
            returns=returns,
            trades=trades,
            metrics=metrics,
        )

    def _calculate_metrics(
        self,
        equity: pd.Series,
        returns: pd.Series,
        trades: pd.DataFrame,
    ) -> Dict[str, float]:
        """Compute standard performance metrics."""
        total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
        days = (equity.index[-1] - equity.index[0]).days
        years = days / 365.25
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        volatility = returns.std() * np.sqrt(252)
        sharpe = (annualized_return / volatility) if volatility > 0 else 0

        # Max drawdown
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_dd = drawdown.min()

        # Trade statistics
        n_trades = len(trades)
        win_rate = np.nan
        if n_trades >= 2:
            # Simple P&L per round trip
            buys = trades[trades["action"] == "BUY"]["price"].values
            sells = trades[trades["action"] == "SELL"]["price"].values
            n_pairs = min(len(buys), len(sells))
            if n_pairs > 0:
                pnls = sells[:n_pairs] - buys[:n_pairs]
                win_rate = (pnls > 0).mean()

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "n_trades": n_trades,
            "win_rate": win_rate if not np.isnan(win_rate) else 0.0,
            "final_equity": equity.iloc[-1],
        }

    def plot(self, result: BacktestResult, title: str = "Backtest Results") -> None:
        """Plot equity curve vs buy & hold (optional enhancement)."""
        fig, ax = plt.subplots(figsize=(12, 6))
        result.equity_curve.plot(ax=ax, label="Strategy", linewidth=1.5)
        ax.set_title(title)
        ax.set_ylabel("Equity ($)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def print_metrics(self, result: BacktestResult) -> None:
        """Pretty-print performance metrics."""
        m = result.metrics
        print("\n" + "=" * 50)
        print(" BACKTEST PERFORMANCE")
        print("=" * 50)
        print(f"Final Equity        : ${m['final_equity']:,.2f}")
        print(f"Total Return        : {m['total_return']:.2%}")
        print(f"Annualized Return   : {m['annualized_return']:.2%}")
        print(f"Volatility (ann.)   : {m['volatility']:.2%}")
        print(f"Sharpe Ratio        : {m['sharpe_ratio']:.2f}")
        print(f"Max Drawdown        : {m['max_drawdown']:.2%}")
        print(f"Number of Trades    : {m['n_trades']}")
        print(f"Win Rate            : {m['win_rate']:.1%}")
        print("=" * 50 + "\n")
