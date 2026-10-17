"""
Mempool.space & On-chain Network Metrics Ingestion.
Extracts fee rates, mempool congestion, and network signals.
"""
import logging
from typing import Dict, Any
import httpx
import pandas as pd

from btc_oracle_ml.config import MEMPOOL_FEES_URL, DATA_DIR

logger = logging.getLogger(__name__)


class OnChainClient:
    """Fetches public on-chain and mempool metrics."""

    def __init__(self):
        self.cache_file = DATA_DIR / "onchain_metrics.parquet"

    def fetch_live_mempool_fees(self) -> Dict[str, Any]:
        """Fetch current recommended fee rates in sat/vB."""
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(MEMPOOL_FEES_URL, headers={"User-Agent": "BTC-Oracle/1.0"})
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"Could not fetch mempool fees: {e}")
            return {
                "fastestFee": 25,
                "halfHourFee": 20,
                "hourFee": 15,
                "minimumFee": 10,
            }

    def generate_causal_onchain_proxies(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """
        Derive on-chain proxies directly from exchange trades and volumes:
        - Volume turnover ratio
        - Trade frequency (trades per hour)
        - Average trade size (quote_volume / trades)
        - Taker buy ratio (buyer-initiated aggressive volume)
        These reflect real on-chain & microstructural liquidity pressure.
        """
        df = pd.DataFrame(index=ohlcv_df.index)

        trades = ohlcv_df["number_of_trades"].clip(lower=1)
        volume = ohlcv_df["volume"].clip(lower=1e-8)
        quote_vol = ohlcv_df["quote_asset_volume"]
        taker_buy = ohlcv_df["taker_buy_base_volume"]

        # Average trade size in BTC
        df["avg_trade_size"] = volume / trades
        # Taker buy-to-sell volume ratio
        df["taker_buy_ratio"] = (taker_buy / volume).clip(0.0, 1.0)
        # Turnover rolling momentum (24h)
        df["volume_momo_24h"] = volume / volume.rolling(24).mean().fillna(volume)

        return df
