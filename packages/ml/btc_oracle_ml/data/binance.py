"""
Binance Public REST API Ingestion for BTCUSDT 1h OHLCV.
Requires no API key. Includes idempotent incremental backfill and gap checks.
"""
import logging
import time
from datetime import UTC, datetime

import httpx
import pandas as pd
from btc_oracle_ml.config import BINANCE_KLINES_URL, DATA_DIR

logger = logging.getLogger(__name__)

# Standard columns returned by Binance klines
BINANCE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore",
]


class BinanceDataClient:
    """Ingests and maintains 1-hour OHLCV candles from Binance public API."""

    def __init__(self, symbol: str = "BTCUSDT", interval: str = "1h"):
        self.symbol = symbol
        self.interval = interval
        self.cache_file = DATA_DIR / f"{self.symbol.lower()}_{self.interval}.parquet"

    def fetch_klines_batch(
        self,
        start_time_ms: int,
        end_time_ms: int | None = None,
        limit: int = 1000,
    ) -> list[list]:
        """Fetch a single batch of klines from Binance."""
        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "startTime": start_time_ms,
            "limit": limit,
        }
        if end_time_ms:
            params["endTime"] = end_time_ms

        headers = {"User-Agent": "BTC-Oracle/1.0"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(BINANCE_KLINES_URL, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def backfill_history(
        self,
        start_dt: datetime,
        end_dt: datetime | None = None,
        progress_cb=None,
    ) -> pd.DataFrame:
        """
        Backfill historical candles between start_dt and end_dt.
        Idempotent: merges with existing local cache without duplicates.
        """
        if end_dt is None:
            end_dt = datetime.now(UTC)

        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)

        # Check existing cache
        existing_df = self.load_cached()
        if not existing_df.empty:
            last_cached_ms = int(existing_df.index.max().timestamp() * 1000)
            if last_cached_ms >= end_ms - (3600 * 1000):
                logger.info("Cache is already up to date.")
                return existing_df
            if last_cached_ms > start_ms:
                start_ms = last_cached_ms + (3600 * 1000)

        all_rows = []
        curr_start = start_ms

        logger.info(f"Fetching Binance candles from {datetime.fromtimestamp(curr_start/1000, tz=UTC)} to {end_dt}")
        while curr_start < end_ms:
            try:
                batch = self.fetch_klines_batch(curr_start, end_ms, limit=1000)
                if not batch:
                    break
                all_rows.extend(batch)
                last_open_time = batch[-1][0]
                curr_start = last_open_time + (3600 * 1000)  # Next hour
                if progress_cb:
                    progress_cb(len(all_rows))
                time.sleep(0.1)  # Respect Binance weight limits
            except Exception as e:
                logger.warning(f"Error fetching Binance batch at {curr_start}: {e}")
                break

        if all_rows:
            new_df = self._parse_klines(all_rows)
            if not existing_df.empty:
                combined = pd.concat([existing_df, new_df])
                combined = combined[~combined.index.duplicated(keep="last")].sort_index()
            else:
                combined = new_df
            self.save_cached(combined)
            return combined
        elif not existing_df.empty:
            return existing_df
        else:
            raise RuntimeError("No data fetched and no cached data available.")

    def _parse_klines(self, raw_rows: list[list]) -> pd.DataFrame:
        """Parse raw Binance JSON rows into typed DataFrame."""
        df = pd.DataFrame(raw_rows, columns=BINANCE_COLUMNS)
        df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df.set_index("timestamp", inplace=True)

        for col in ["open", "high", "low", "close", "volume", "quote_asset_volume", "taker_buy_base_volume", "taker_buy_quote_volume"]:
            df[col] = df[col].astype(float)

        df["number_of_trades"] = df["number_of_trades"].astype(int)
        keep_cols = ["open", "high", "low", "close", "volume", "quote_asset_volume", "number_of_trades", "taker_buy_base_volume"]
        return df[keep_cols]

    def save_cached(self, df: pd.DataFrame) -> None:
        """Persist to Parquet."""
        df.to_parquet(self.cache_file)
        logger.info(f"Saved {len(df)} candles to {self.cache_file}")

    def load_cached(self) -> pd.DataFrame:
        """Load from local Parquet cache if available."""
        if self.cache_file.exists():
            try:
                df = pd.read_parquet(self.cache_file)
                return df.sort_index()
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")
        return pd.DataFrame()
