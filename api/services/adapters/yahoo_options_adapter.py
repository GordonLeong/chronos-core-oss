import logging
from datetime import datetime, timezone
import pandas as pd
from yahooquery import Ticker

from services.contracts import OptionChainAdapter, OptionChainSnapshot, OptionStrike
from services.adapter_registry import register_option_adapter

logger = logging.getLogger(__name__)

class YahooOptionsAdapter(OptionChainAdapter):
    """
    Implements OptionChainAdapter utilizing yahooquery to fetch option chains.
    """
    def fetch_chain_snapshot(self, ticker: str) -> OptionChainSnapshot:
        tk = Ticker(ticker, asynchronous=False)
        chain_df = tk.option_chain
        
        # Returns a dict of empty DataFrames or a MultiIndex DataFrame if options exist.
        if type(chain_df) is dict or chain_df.empty:
            logger.warning("No options chain returned for %s", ticker)
            return OptionChainSnapshot(
                underlying_ticker=ticker,
                as_of=datetime.now(timezone.utc),
                expiries={}
            )

        # The DataFrame typically has a MultiIndex of (symbol, expiration, optionType).
        # And standard columns: strike, currency, lastPrice, change, percentChange, volume, openInterest, bid, ask, contractSymbol, impliedVolatility, inTheMoney, contractSize, currency
        
        # Reset index to make grouping easier
        chain_df = chain_df.reset_index()
        
        expiries: dict[str, list[OptionStrike]] = {}
        
        # Ensure we have the required columns
        required_cols = {"expiration", "optionType", "strike"}
        if not required_cols.issubset(chain_df.columns):
            logger.error("Missing expected option chain columns for %s", ticker)
            return OptionChainSnapshot(underlying_ticker=ticker, as_of=datetime.now(timezone.utc), expiries={})
        
        # Group by expiration date string
        # typical format of `expiration` in yahooquery is datetime or string 'YYYY-MM-DD'
        
        for exp_val, exp_group in chain_df.groupby("expiration"):
            # Normalize expiration to YYYY-MM-DD
            if isinstance(exp_val, pd.Timestamp) or isinstance(exp_val, datetime):
                exp_str = exp_val.strftime("%Y-%m-%d")
            else:
                exp_str = str(exp_val)[:10]  # Just take the date part
                
            strikes_map: dict[float, OptionStrike] = {}
            
            for _, row in exp_group.iterrows():
                strike = float(row.get("strike", 0.0))
                opt_type = str(row.get("optionType", "")).lower() # "calls" or "puts"
                
                bid = float(row.get("bid", 0.0)) if pd.notna(row.get("bid", 0.0)) else None
                ask = float(row.get("ask", 0.0)) if pd.notna(row.get("ask", 0.0)) else None
                
                mid = None
                if bid is not None and ask is not None and bid >= 0 and ask >= 0:
                    mid = round((bid + ask) / 2.0, 4)
                    
                iv = float(row.get("impliedVolatility", 0.0)) if pd.notna(row.get("impliedVolatility", 0.0)) else None
                
                if strike not in strikes_map:
                    strikes_map[strike] = OptionStrike(
                        strike=strike,
                        call_bid=None, call_ask=None, call_mid=None, call_iv=None,
                        put_bid=None, put_ask=None, put_mid=None, put_iv=None,
                    )
                
                strike_record = strikes_map[strike]
                
                if "call" in opt_type:
                    strike_record.call_bid = bid
                    strike_record.call_ask = ask
                    strike_record.call_mid = mid
                    strike_record.call_iv = iv
                elif "put" in opt_type:
                    strike_record.put_bid = bid
                    strike_record.put_ask = ask
                    strike_record.put_mid = mid
                    strike_record.put_iv = iv
                    
            expiries[exp_str] = sorted(list(strikes_map.values()), key=lambda s: s.strike)
            
        return OptionChainSnapshot(
            underlying_ticker=ticker.upper(),
            as_of=datetime.now(timezone.utc),
            expiries=expiries
        )
