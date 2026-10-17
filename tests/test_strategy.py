"""
Basic unit tests for the SMA Crossover strategy.
"""

import pandas as pd
import pytest

from src.strategy import SMACrossoverStrategy


@pytest.fixture
def sample_data():
    """Create a small synthetic price series."""
    dates = pd.date_range("2023-01-01", periods=250, freq="B")
    # Simple upward then downward trend
    prices = list(range(100, 200)) + list(range(200, 100, -1))
    prices = prices[:250]
    df = pd.DataFrame({"Close": prices}, index=dates)
    return df


def test_strategy_initialization():
    strategy = SMACrossoverStrategy(short_window=50, long_window=200)
    assert strategy.short_window == 50
    assert strategy.long_window == 200


def test_invalid_windows():
    with pytest.raises(ValueError):
        SMACrossoverStrategy(short_window=200, long_window=50)


def test_generate_signals(sample_data):
    strategy = SMACrossoverStrategy(short_window=10, long_window=30)
    result = strategy.generate_signals(sample_data)

    assert f"SMA_10" in result.columns
    assert f"SMA_30" in result.columns
    assert "Signal" in result.columns
    assert "Position" in result.columns

    # Signals should only be -1, 0 or 1
    assert set(result["Signal"].unique()).issubset({-1, 0, 1})


def test_get_latest_signal(sample_data):
    strategy = SMACrossoverStrategy(short_window=10, long_window=30)
    signal = strategy.get_latest_signal(sample_data)
    assert signal is not None
    assert signal.action in {"BUY", "SELL", "HOLD"}
