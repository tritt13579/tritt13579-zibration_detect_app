"""Data preprocessing for vibration signal inference."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import torch


def select_dx_columns(df: pd.DataFrame) -> np.ndarray:
    """Extract DX columns from Excel DataFrame.
    
    Matches the logic in convert_dulieu71Hz_to_npy.py:
    - First tries to select columns containing "DX" in the name
    - Falls back to columns at indices [1, 3, 5] if no DX columns found
    
    Args:
        df: Input DataFrame from Excel file
        
    Returns:
        Numpy array of shape (T, C) where T is time steps and C is channels
        
    Raises:
        ValueError: If cannot infer DX columns
    """
    dx_cols = [c for c in df.columns if isinstance(c, str) and ("DX" in c.upper())]
    if dx_cols:
        return df.loc[:, dx_cols].to_numpy(dtype=np.float32)

    if df.shape[1] >= 6:
        idx = [1, 3, 5]
        return df.iloc[:, idx].to_numpy(dtype=np.float32)

    raise ValueError(f"Cannot infer DX columns from columns={df.columns.tolist()}")


def create_windows(
    data: np.ndarray,
    window: int,
    step: int,
) -> list[np.ndarray]:
    """Create sliding windows from time series data.
    
    Args:
        data: Input array of shape (T, C) where T is time steps, C is channels
        window: Window size
        step: Step size between windows
        
    Returns:
        List of windows, each of shape (T_window, C)
    """
    n_samples = data.shape[0]
    if n_samples < window:
        return []
    
    windows = []
    for start in range(0, n_samples - window + 1, step):
        end = start + window
        w = data[start:end, :]
        if w.shape[0] == window:
            windows.append(w.astype(np.float32))
    
    return windows


def normalize_windows(
    windows: list[np.ndarray],
    mean: np.ndarray,
    std: np.ndarray,
    eps: float = 1e-8,
) -> list[np.ndarray]:
    """Normalize windows using mean and std from training.
    
    Args:
        windows: List of windows, each of shape (T, C)
        mean: Mean values per channel, shape (C,)
        std: Std values per channel, shape (C,)
        eps: Small value to avoid division by zero
        
    Returns:
        List of normalized windows, each of shape (T, C)
    """
    normalized = []
    for w in windows:
        w_norm = (w - mean[None, :]) / (std[None, :] + eps)
        normalized.append(w_norm.astype(np.float32))
    return normalized


def windows_to_tensors(
    windows: list[np.ndarray],
    return_ct: bool = True,
) -> torch.Tensor:
    """Convert windows to PyTorch tensor batch.
    
    Args:
        windows: List of windows, each of shape (T, C)
        return_ct: If True, transpose to (C, T) format
        
    Returns:
        Tensor of shape (N, C, T) if return_ct=True, else (N, T, C)
    """
    if not windows:
        raise ValueError("No windows to convert")
    
    batch = []
    for w in windows:
        if return_ct:
            w = w.T  # (C, T)
        batch.append(w)
    
    return torch.from_numpy(np.stack(batch, axis=0))


def preprocess_excel_for_inference(
    df: pd.DataFrame,
    window: int,
    step: int,
    mean: np.ndarray,
    std: np.ndarray,
    channels: int,
    eps: float = 1e-8,
) -> tuple[torch.Tensor, int]:
    """Complete preprocessing pipeline for inference.
    
    Args:
        df: Input DataFrame from Excel
        window: Window size
        step: Step size
        mean: Mean values per channel from training
        std: Std values per channel from training
        channels: Expected number of channels
        eps: Small value for normalization
        
    Returns:
        Tuple of (batch_tensor, num_windows) where:
        - batch_tensor: shape (N, C, T)
        - num_windows: number of windows created
        
    Raises:
        ValueError: If data shape doesn't match expected channels
    """
    data = select_dx_columns(df)
    
    if data.shape[1] != channels:
        raise ValueError(
            f"Expected {channels} channels, got {data.shape[1]} channels"
        )
    
    windows = create_windows(data, window, step)
    
    if not windows:
        raise ValueError(
            f"Not enough data for windowing. Need at least {window} samples, "
            f"got {data.shape[0]} samples"
        )
    
    windows = normalize_windows(windows, mean, std, eps)
    batch = windows_to_tensors(windows, return_ct=True)
    
    return batch, len(windows)
