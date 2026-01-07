# data_collector.py

import ccxt
from typing import List, Dict, Any


class DataCollector:
    """
    A class to collect market data from cryptocurrency exchanges using the CCXT library.
    """

    def __init__(self, exchange_name: str, symbol: str, timeframe: str = '1h') -> None:
        """
        Initializes the DataCollector with the specified exchange, trading pair symbol, and timeframe.

        :param exchange_name: The name of the exchange to connect to.
        :param symbol: The trading pair symbol, e.g., 'BTC/USDT'.
        :param timeframe: The timeframe for the OHLCV data, default is '1h'.
        """
        self.exchange = getattr(ccxt, exchange_name)()
        self.symbol = symbol
        self.timeframe = timeframe

    def fetch_ohlcv(self, limit: int = 100) -> List[List[Any]]:
        """
        Fetches OHLCV data for the specified trading pair and timeframe.

        :param limit: The number of data points to fetch, default is 100.
        :return: A list of OHLCV data points.
        """
        try:
            data = self.exchange.fetch_ohlcv(self.symbol, timeframe=self.timeframe, limit=limit)
            return data
        except ccxt.BaseError as e:
            print(f"An error occurred: {e}")
            return []


if __name__ == "__main__":
    # Demo usage of DataCollector
    collector = DataCollector(exchange_name='binance', symbol='BTC/USDT')
    ohlcv_data = collector.fetch_ohlcv()
    print(ohlcv_data)