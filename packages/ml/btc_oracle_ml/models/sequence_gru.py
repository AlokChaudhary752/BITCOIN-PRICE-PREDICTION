"""
PyTorch Stacked GRU Sequence Model with Quantile Pinball Loss.
Processes rolling time series windows with self-attention for probabilistic forecasting.
"""
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from btc_oracle_ml.config import QUANTILES


class PinballLoss(nn.Module):
    """Multi-quantile pinball loss: sum_q max(q*(y - y_hat), (q-1)*(y - y_hat))."""

    def __init__(self, quantiles: List[float]):
        super().__init__()
        self.quantiles = quantiles

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        # y_pred: (batch, num_quantiles), y_true: (batch, 1)
        loss = torch.tensor(0.0, device=y_pred.device)
        for i, q in enumerate(self.quantiles):
            error = y_true - y_pred[:, i : i + 1]
            q_loss = torch.max(q * error, (q - 1.0) * error)
            loss += torch.mean(q_loss)
        return loss


class AttentionPooling(nn.Module):
    """Temporal attention pooling over sequence length."""

    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, rnn_out: torch.Tensor) -> torch.Tensor:
        # rnn_out: (batch, seq_len, hidden_dim)
        scores = self.attn(rnn_out)  # (batch, seq_len, 1)
        weights = torch.softmax(scores, dim=1)
        context = torch.sum(weights * rnn_out, dim=1)  # (batch, hidden_dim)
        return context


class QuantileGRU(nn.Module):
    """Stacked GRU architecture with attention and quantile output heads."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_quantiles: int = 5,
        dropout: float = 0.15,
    ):
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.attention = AttentionPooling(hidden_dim)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, num_quantiles),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_dim)
        rnn_out, _ = self.gru(x)
        context = self.attention(rnn_out)
        out = self.fc(context)  # (batch, num_quantiles)
        return out


class SequenceGRUModel:
    """Wrapper managing dataset sliding windows, training, and quantile inference."""

    def __init__(
        self,
        horizon_name: str,
        seq_len: int = 24,
        hidden_dim: int = 48,
        quantiles: Optional[List[float]] = None,
        batch_size: int = 128,
        epochs: int = 10,
        learning_rate: float = 0.003,
    ):
        self.horizon_name = horizon_name
        self.seq_len = seq_len
        self.hidden_dim = hidden_dim
        self.quantiles = quantiles or QUANTILES
        self.batch_size = batch_size
        self.epochs = epochs
        self.lr = learning_rate

        self.net: Optional[QuantileGRU] = None
        self.means: Optional[np.ndarray] = None
        self.stds: Optional[np.ndarray] = None
        self.feature_names_: List[str] = []

    def _create_sequences(
        self,
        X_vals: np.ndarray,
        y_vals: Optional[np.ndarray] = None,
    ):
        n_samples = len(X_vals) - self.seq_len + 1
        if n_samples <= 0:
            raise ValueError(f"Sequence length {self.seq_len} exceeds total samples {len(X_vals)}")

        X_seq = np.zeros((n_samples, self.seq_len, X_vals.shape[1]), dtype=np.float32)
        for i in range(n_samples):
            X_seq[i] = X_vals[i : i + self.seq_len]

        if y_vals is not None:
            y_seq = y_vals[self.seq_len - 1 :].astype(np.float32).reshape(-1, 1)
            return X_seq, y_seq
        return X_seq

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "SequenceGRUModel":
        self.feature_names_ = list(X.columns)

        # Standardize strictly on training set
        X_arr = X.values.astype(np.float32)
        y_arr = y.values.astype(np.float32)

        valid_mask = ~(np.isnan(y_arr) | np.isinf(y_arr))
        # Keep index alignment
        first_valid_idx = np.where(valid_mask)[0]
        if len(first_valid_idx) == 0:
            return self

        max_valid_idx = first_valid_idx[-1] + 1
        X_arr = X_arr[:max_valid_idx]
        y_arr = y_arr[:max_valid_idx]

        self.means = np.nanmean(X_arr, axis=0)
        self.stds = np.nanstd(X_arr, axis=0) + 1e-6
        X_norm = (X_arr - self.means) / self.stds

        X_seq, y_seq = self._create_sequences(X_norm, y_arr)

        # Filter any sequences with nan targets
        keep = ~np.isnan(y_seq.ravel())
        X_seq = X_seq[keep]
        y_seq = y_seq[keep]

        dataset = TensorDataset(torch.from_numpy(X_seq), torch.from_numpy(y_seq))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        self.net = QuantileGRU(
            input_dim=len(self.feature_names_),
            hidden_dim=self.hidden_dim,
            num_quantiles=len(self.quantiles),
        )
        optimizer = torch.optim.Adam(self.net.parameters(), lr=self.lr, weight_decay=1e-5)
        criterion = PinballLoss(self.quantiles)

        self.net.train()
        for epoch in range(self.epochs):
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                preds = self.net(batch_x)
                loss = criterion(preds, batch_y)
                loss.backward()
                optimizer.step()

        return self

    def predict_quantiles(self, X: pd.DataFrame) -> Dict[float, np.ndarray]:
        """Inference on input dataframe."""
        if self.net is None or self.means is None:
            zeros = np.zeros(len(X))
            return {q: zeros for q in self.quantiles}

        self.net.eval()
        X_arr = X.values.astype(np.float32)
        X_norm = (X_arr - self.means) / self.stds

        # If length is smaller than seq_len, repeat initial row to reach seq_len
        if len(X_norm) < self.seq_len:
            pad = np.tile(X_norm[0], (self.seq_len - len(X_norm), 1))
            X_norm = np.vstack([pad, X_norm])

        X_seq = self._create_sequences(X_norm)
        with torch.no_grad():
            preds = self.net(torch.from_numpy(X_seq)).cpu().numpy()

        # Sort quantiles to enforce non-crossing
        sorted_preds = np.sort(preds, axis=1)

        # Align back to len(X)
        if len(sorted_preds) < len(X):
            pad_count = len(X) - len(sorted_preds)
            pad_block = np.repeat(sorted_preds[0:1], pad_count, axis=0)
            sorted_preds = np.vstack([pad_block, sorted_preds])

        result: Dict[float, np.ndarray] = {}
        for i, q in enumerate(self.quantiles):
            result[q] = sorted_preds[:, i]

        return result
