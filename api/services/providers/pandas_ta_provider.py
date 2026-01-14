from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import pandas as pd
import pandas_ta as ta

from ohlcv import OHLCVRow
from services.signals import SignalRow
from services.ta_registry import register_ta_provider


def _to_float(value: Optional[float]) -> Optional[float]:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _to_date(value: object) -> date:
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


class PandasTAProvider:
    name = "pandas_ta"

    def compute_signals(self, rows: list[OHLCVRow]) -> list[SignalRow]:
        if not rows:
            return []

        df = pd.DataFrame(
            rows, columns=["date", "open", "high", "low", "close", "volume"]
        ).set_index("date").sort_index()

        close = df["close"]

        df["rsi"] = ta.rsi(close, length=14)

        macd = ta.macd(close)
        if macd is not None and not macd.empty:
            df["macd"] = macd.iloc[:, 0]
            df["macd_signal"] = macd.iloc[:, 1]
        else:
            df["macd"] = None
            df["macd_signal"] = None

        df["ema_20"] = ta.ema(close, length=20)
        df["ema_50"] = ta.ema(close, length=50)

        bb = ta.bbands(close, length=20, std=2.0)  # type: ignore[arg-type]
        if bb is not None and not bb.empty:
            df["bb_lower"] = bb.iloc[:, 0]
            df["bb_upper"] = bb.iloc[:, 2]
        else:
            df["bb_lower"] = None
            df["bb_upper"] = None

        required = ["rsi", "macd", "macd_signal", "ema_20", "ema_50", "bb_upper", "bb_lower"]
        signal_rows: list[SignalRow] = []

        for idx, row in df.iterrows():
            if any(pd.isna(row[col]) for col in required):
                continue
            as_of: date = _to_date(idx)
            signal_rows.append(
                (
                    as_of,
                    _to_float(row["rsi"]),
                    _to_float(row["macd"]),
                    _to_float(row["macd_signal"]),
                    _to_float(row["ema_20"]),
                    _to_float(row["ema_50"]),
                    _to_float(row["bb_upper"]),
                    _to_float(row["bb_lower"]),
                )
            )

        return signal_rows


register_ta_provider(PandasTAProvider())
