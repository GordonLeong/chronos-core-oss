from __future__ import annotations
from yahooquery import Ticker
from services.provider_registry import PriceProvider, register_provider
from datetime import date, datetime
from typing import Optional, List, cast
import pandas as pd
from yahooquery import Ticker

from ohlcv import OHLCVRow


class YahooQueryProvider:
    """
    YahooQuery adapter implementing PriceProvider interface.
    """
    name = "yahooquery"

    def fetch_ohlcv(self, ticker:str, interval: str) -> int:
        """
        Backwards-Compatible: return the number of rows fetch, done by 
        fetch_ohlcv_rows()
    
        """
        rows = self.fetch_ohlcv_rows(ticker, interval)
        return len(rows)
    
    def fetch_ohlcv_rows(
            self,
            ticker: str,
            interval: str,
    ) -> List[OHLCVRow]:
        """
        Fetch OHLCV data from yahooquery and normalise into 
        (date, open, high, low, close, volume) tuples
        Volume may be None, if not available
        """
        tk = Ticker(ticker, asynchronous=False)
        data = tk.history(interval="3mo")

        rows: List[OHLCVRow] = []

        if isinstance(data, pd.DataFrame):
            df = data

            if isinstance(df.index, pd.MultiIndex):
                try:
                    df = df.xs(ticker, level=0)
                except KeyError:
                    return []

            df = df.copy()
            for idx, r in df.iterrows():
                # idx can be Timestamp, datetime, or date; normalize to date
                if isinstance(idx, pd.Timestamp):
                    dt = idx.date()
                elif isinstance(idx, datetime):
                    dt = idx.date()
                elif isinstance(idx, date):
                    dt = idx
                else:
                    # last-resort parse; shouldn't usually hit this
                    dt = date.fromisoformat(str(idx))

                   
                o = float(r["open"])
                h = float(r["high"])
                l = float(r["low"])
                c = float(r["close"])
                v: Optional[float] = None
                if "volume" in r and pd.notna(r["volume"]):
                    v = float(r["volume"])
                rows.append((dt, o, h, l, c, v))

            return rows

        if isinstance(data, dict):
            inner = data.get(ticker)
            if isinstance(inner, pd.DataFrame):
                df = inner.copy()

                for idx, r in df.iterrows(): # type: ignore[reportGeneralTypeIssues]
                    if isinstance(idx, pd.Timestamp):
                        dt = idx.date()
                    elif isinstance(idx, datetime):
                        dt = idx.date()
                    elif isinstance(idx, date):
                        dt = idx
                    else:
                        dt = date.fromisoformat(str(idx))

                    o = float(r["open"])
                    h = float(r["high"])
                    l = float(r["low"])
                    c = float(r["close"])
                    v: Optional[float] = None
                    if "volume" in r and pd.notna(r["volume"]):
                        v = float(r["volume"])
                    rows.append((dt, o, h, l, c, v))
                rows.sort(key=lambda tup: tup[0])
                return rows
        # Fallback: unrecognized shape or empty → no rows
        return rows


register_provider(YahooQueryProvider())