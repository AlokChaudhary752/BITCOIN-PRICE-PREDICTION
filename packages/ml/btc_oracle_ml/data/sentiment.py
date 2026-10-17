"""
Alternative.me Fear and Greed Index Ingestion.
Historical daily index scaled to hourly series.
"""
import logging

import httpx
import pandas as pd
from btc_oracle_ml.config import DATA_DIR, FEAR_GREED_URL

logger = logging.getLogger(__name__)


class FearGreedClient:
    """Fetches and caches the Crypto Fear & Greed index."""

    def __init__(self):
        self.cache_file = DATA_DIR / "fear_and_greed.parquet"

    def fetch_history(self) -> pd.DataFrame:
        """Fetch all historical records from Alternative.me."""
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(FEAR_GREED_URL, headers={"User-Agent": "BTC-Oracle/1.0"})
                resp.raise_for_status()
                data = resp.json().get("data", [])

            records = []
            for item in data:
                ts = pd.to_datetime(int(item["timestamp"]), unit="s", utc=True)
                val = float(item["value"])
                records.append({"timestamp": ts, "fear_greed_val": val})

            df = pd.DataFrame(records).set_index("timestamp").sort_index()
            # Normalize to 0..1 range
            df["fear_greed_norm"] = df["fear_greed_val"] / 100.0
            self.save_cached(df)
            return df
        except Exception as e:
            logger.warning(f"Could not fetch live Fear & Greed: {e}. Falling back to cached.")
            cached = self.load_cached()
            if not cached.empty:
                return cached
            # If no network and no cache, construct default neutral series
            return pd.DataFrame()

    def align_to_hourly(self, ohlcv_index: pd.DatetimeIndex) -> pd.DataFrame:
        """Align daily fear & greed data forward-filled to hourly index."""
        fg_df = self.load_cached()
        if fg_df.empty:
            fg_df = self.fetch_history()

        if fg_df.empty:
            # Fallback neutral 0.5
            return pd.DataFrame(
                {"fear_greed_norm": 0.5, "fear_greed_val": 50.0},
                index=ohlcv_index,
            )

        # Reindex to hourly and forward fill (strictly causal)
        aligned = fg_df.reindex(ohlcv_index.union(fg_df.index)).ffill().bfill()
        return aligned.loc[ohlcv_index]

    def save_cached(self, df: pd.DataFrame) -> None:
        df.to_parquet(self.cache_file)

    def load_cached(self) -> pd.DataFrame:
        if self.cache_file.exists():
            try:
                return pd.read_parquet(self.cache_file).sort_index()
            except Exception as e:
                logger.warning(f"Failed loading FG cache: {e}")
        return pd.DataFrame()
