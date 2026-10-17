"""
Paper Trading client for Interactive Brokers using the official ibapi.

Requirements:
- TWS or IB Gateway running and logged into a PAPER account
- API enabled on port 7497 (default for paper)
"""

import threading
import time
from typing import Optional

import pandas as pd

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.wrapper import EWrapper

from src.strategy import SMACrossoverStrategy, Signal
from src.utils import setup_logging

logger = setup_logging()


class IBPaperTrader(EWrapper, EClient):
    """
    Connects to Interactive Brokers paper trading account
    and executes the SMA Crossover strategy.
    """

    def __init__(
        self,
        strategy: SMACrossoverStrategy,
        symbol: str = "AAPL",
        quantity: int = 100,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
    ):
        EClient.__init__(self, self)
        self.strategy = strategy
        self.symbol = symbol
        self.quantity = quantity
        self.host = host
        self.port = port
        self.client_id = client_id

        self.next_order_id: Optional[int] = None
        self.historical_data: list[dict] = []
        self.current_position: int = 0  # 0 = flat, >0 = long shares
        self._data_ready = threading.Event()

    # ------------------------------------------------------------------
    # IB API callbacks
    # ------------------------------------------------------------------
    def nextValidId(self, orderId: int):
        self.next_order_id = orderId
        logger.info(f"Next valid order ID: {orderId}")

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        # Filter out common informational messages
        if errorCode in (2104, 2106, 2158, 2119):  # market data / connection info
            logger.debug(f"IB Info {errorCode}: {errorString}")
        else:
            logger.error(f"IB Error {errorCode} | reqId={reqId} | {errorString}")

    def historicalData(self, reqId, bar):
        self.historical_data.append(
            {
                "Date": pd.to_datetime(bar.date),
                "Open": bar.open,
                "High": bar.high,
                "Low": bar.low,
                "Close": bar.close,
                "Volume": bar.volume,
            }
        )

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        logger.info(f"Historical data received ({len(self.historical_data)} bars)")
        self._data_ready.set()

    def orderStatus(
        self,
        orderId,
        status,
        filled,
        remaining,
        avgFillPrice,
        permId,
        parentId,
        lastFillPrice,
        clientId,
        whyHeld,
        mktCapPrice,
    ):
        logger.info(
            f"Order {orderId} | Status: {status} | Filled: {filled} @ {avgFillPrice}"
        )

    def position(self, account, contract, position, avgCost):
        if contract.symbol == self.symbol:
            self.current_position = int(position)
            logger.info(f"Current position in {self.symbol}: {self.current_position}")

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def connect_and_start(self):
        """Connect to TWS/IB Gateway and start the API thread."""
        logger.info(f"Connecting to IBKR at {self.host}:{self.port} ...")
        self.connect(self.host, self.port, self.client_id)

        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        time.sleep(1)  # allow connection to establish

        if not self.isConnected():
            raise ConnectionError("Could not connect to Interactive Brokers")

        logger.info("Connected successfully")

    def request_historical_data(self, duration: str = "1 Y", bar_size: str = "1 day"):
        """Request historical bars needed for the SMAs."""
        self.historical_data = []
        self._data_ready.clear()

        contract = self._create_contract()
        self.reqHistoricalData(
            reqId=1,
            contract=contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[],
        )

        # Wait until data arrives (timeout 30s)
        if not self._data_ready.wait(timeout=30):
            raise TimeoutError("Timeout waiting for historical data")

        df = pd.DataFrame(self.historical_data)
        df.set_index("Date", inplace=True)
        return df

    def evaluate_and_trade(self):
        """
        Fetch latest data, compute signal and place order if needed.
        Call this periodically (e.g. once per day after market close).
        """
        df = self.request_historical_data(duration="1 Y", bar_size="1 day")
        signal: Optional[Signal] = self.strategy.get_latest_signal(df)

        if signal is None:
            logger.info("Not enough data to generate signal")
            return

        logger.info(
            f"Signal: {signal.action} | Price: {signal.price:.2f} | "
            f"SMA{self.strategy.short_window}: {signal.short_sma:.2f} | "
            f"SMA{self.strategy.long_window}: {signal.long_sma:.2f}"
        )

        if signal.action == "BUY" and self.current_position == 0:
            self._place_order("BUY", self.quantity)
        elif signal.action == "SELL" and self.current_position > 0:
            self._place_order("SELL", self.current_position)
        else:
            logger.info("No action required")

    def _create_contract(self) -> Contract:
        contract = Contract()
        contract.symbol = self.symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def _place_order(self, action: str, quantity: int):
        if self.next_order_id is None:
            logger.error("No valid order ID available")
            return

        contract = self._create_contract()
        order = Order()
        order.action = action
        order.orderType = "MKT"
        order.totalQuantity = quantity
        order.eTradeOnly = False
        order.firmQuoteOnly = False

        logger.info(f"Placing {action} order for {quantity} shares of {self.symbol}")
        self.placeOrder(self.next_order_id, contract, order)
        self.next_order_id += 1

    def disconnect_gracefully(self):
        logger.info("Disconnecting from IBKR...")
        self.disconnect()
