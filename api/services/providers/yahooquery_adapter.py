from __future__ import annotations
from yahooquery import Ticker
from services.provider_registry import PriceProvider, register_provider


class YahooQueryProvider:
    """
    YahooQuery adapter implementing PriceProvider interface.
    """
    name = "yahooquery"

    def fetch_ohlcv(self, ticker:str, interval: str) -> int:
        """
        Fetch OHLCV bars via yahooquery. Return count of rows. 
        Raise on network/provider errors
    
        """

        tk = Ticker(ticker, asynchronous=False)
        data = tk.history(interval=interval)


        if hasattr(data, "reset_index"):
            return len(data)
        
        if isinstance(data, dict):
            for _, v in data.items():
                if hasattr(v, "reset_index"):
                    return len(v)
                
        return 0


register_provider(YahooQueryProvider())