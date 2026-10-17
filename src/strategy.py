"""
SMA Crossover Strategy

Buy signal  : short SMA crosses above long SMA
Sell signal : short SMA crosses below long SMA
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class Signal:
    """Trading signal representation."""
    timestamp: pd.Timestamp
    action: str          # "BUY", "SELL", "HOLD"
    price: float
    short_sma: float
    long_sma: float


class SMACrossoverStrategy:
    """
    Classic dual moving average crossover strategy.

    Parameters
    ----------
    short_window : int
        Period for the fast SMA (default 50).
    long_window : int
        Period for the slow SMA (default 200).
    """

    def __init__(self, short_window: int = 50, long_window: int = 200):
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")
        self.short_window = short_window
        self.long_window = long_window
        self.name = f"SMA_{short_window}_{long_window}"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate SMAs and generate trading signals.

        Expected columns: ['Close'] (or 'close').
        Returns a copy of the DataFrame with added columns:
            - SMA_short, SMA_long
            - Signal          (1 = buy crossover, -1 = sell crossover, 0 = no change)
            - Position        (current position after signal)
        """
        data = df.copy()

        # Normalize column names
        if "Close" not in data.columns and "close" in data.columns:
            data["Close"] = data["close"]

        data[f"SMA_{self.short_window}"] = (
            data["Close"].rolling(window=self.short_window, min_periods=self.short_window).mean()
        )
        data[f"SMA_{self.long_window}"] = (
            data["Close"].rolling(window=self.long_window, min_periods=self.long_window).mean()
        )

        # Raw signal: 1 when short > long, else -1
        data["raw_signal"] = 0
        data.loc[
            data[f"SMA_{self.short_window}"] > data[f"SMA_{self.long_window}"],
            "raw_signal",
        ] = 1
        data.loc[
            data[f"SMA_{self.short_window}"] < data[f"SMA_{self.long_window}"],
            "raw_signal",
        ] = -1

        # Position changes only on crossover
        data["Signal"] = data["raw_signal"].diff().fillna(0)
        # Convert to clean signals: +2 → BUY, -2 → SELL (because 1 - (-1) = 2)
        data["Signal"] = data["Signal"].map({2: 1, -2: -1}).fillna(0).astype(int)

        # Current position (forward fill of last non-zero raw signal)
        # Avoid deprecated method= parameter
        data["Position"] = data["raw_signal"].replace(0, pd.NA).ffill().fillna(0).astype(int)

        return data

    def get_latest_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        """
        Return the most recent actionable signal (BUY / SELL), or None.
        Useful for live / paper trading.
        """
        signals = self.generate_signals(df)
        if len(signals) < 2:
            return None

        last = signals.iloc[-1]
        prev = signals.iloc[-2]

        short_col = f"SMA_{self.short_window}"
        long_col = f"SMA_{self.long_window}"

        # Detect crossover
        if last[short_col] > last[long_col] and prev[short_col] <= prev[long_col]:
            action = "BUY"
        elif last[short_col] < last[long_col] and prev[short_col] >= prev[long_col]:
            action = "SELL"
        else:
            action = "HOLD"

        return Signal(
            timestamp=last.name if isinstance(last.name, pd.Timestamp) else pd.Timestamp.now(),
            action=action,
            price=float(last["Close"]),
            short_sma=float(last[short_col]),
            long_sma=float(last[long_col]),
        )
