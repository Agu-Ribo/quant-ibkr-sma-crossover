"""
Data fetching utilities.
Primary source for backtesting: yfinance.
IBKR historical data can be added later if needed.
"""

from typing import Optional

import pandas as pd
import yfinance as yf

from src.utils import setup_logging

logger = setup_logging()


def fetch_ohlcv(
    symbol: str,
    start: str = "2020-01-01",
    end: Optional[str] = None,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Download OHLCV data using yfinance.

    Parameters
    ----------
    symbol : str
        Ticker symbol (e.g. "AAPL").
    start : str
        Start date (YYYY-MM-DD).
    end : str, optional
        End date (YYYY-MM-DD). If None, downloads until today.
    interval : str
        Bar size ("1d", "1h", etc.).

    Returns
    -------
    pd.DataFrame
        Columns: Open, High, Low, Close, Volume, Adj Close
    """
    logger.info(f"Downloading {symbol} from {start} to {end or 'today'}...")
    data = yf.download(
        symbol,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )

    if data.empty:
        raise ValueError(f"No data returned for {symbol}")

    # Flatten multi-index columns if present (newer yfinance versions)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.dropna()
    logger.info(f"Downloaded {len(data)} bars for {symbol}")
    return data
