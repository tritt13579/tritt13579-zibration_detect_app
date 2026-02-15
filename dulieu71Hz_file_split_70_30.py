# dulieu71Hz_file_split_70_30.py
import os
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader


# =========================
# CONFIG
# =========================
@dataclass
class Dulieu71HzCfg:
    root: str = "./Dulieu/dulieu71Hz"

    channels: int = 3
    window: int = 2048
    step: int = 2048
    seed: int = 42

    normalize: bool = True
    eps: float = 1e-8
    return_ct: bool = True  # True: (C,T), False: (T,C)

    # augmentation (paper-style) - offline expansion (TRAIN only)
    noise_ks: tuple = (0.03, 0.05, 0.07)


# =========================
# UTIL
# =========================
def _starts(n_samples: int, window: int, step: int) -> List[int]:
    if n_samples < window:
        return []
    return list(range(0, n_samples - window + 1, step))


def _list_npy_files(cfg: Dulieu71HzCfg, cls: str) -> List[str]:
    d = os.path.join(cfg.root, cls)
    if not os.path.isdir(d):
        raise FileNotFoundError(f"Missing class dir: {d}")
    files = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(".npy")]
    if not files:
        raise FileNotFoundError(f"No .npy files in: {d}. Run convert_dulieu71Hz_to_npy.py first!")
    return files


def _load_npy_mmap(fp: str, cache: Dict, expected_channels: Optional[int]) -> np.ndarray:
    if fp in cache:
        arr = cache[fp]
        if expected_channels is not None and int(arr.shape[1]) != int(expected_channels):
            raise ValueError(f"{fp}: expected C={expected_channels}, got {arr.shape[1]}")
        return arr

    arr = np.load(fp, mmap_mode="r")  # shape (T,C)
    if arr.ndim != 2:
        raise ValueError(f"{fp}: expected 2D array (T,C), got {arr.shape}")
    if expected_channels is not None and int(arr.shape[1]) != int(expected_channels):
        raise ValueError(f"{fp}: expected C={expected_channels}, got {arr.shape[1]}")

    cache[fp] = arr
    return arr


def _load_window(fp: str, start: int, cfg: Dulieu71HzCfg, cache: Dict) -> np.ndarray:
    arr = _load_npy_mmap(fp, cache, expected_channels=cfg.channels)  # (T,C)
    end = start + cfg.window
    w = arr[start:end, :]
    if int(w.shape[0]) != int(cfg.window):
        raise ValueError(f"{fp}: window length mismatch {w.shape[0]} != {cfg.window} (start={start})")
    return np.asarray(w, dtype=np.float32)


def _split_files_70_30(files: List[str], rng: random.Random) -> Tuple[List[str], List[str]]:
    n = len(files)
    if n < 2:
        raise ValueError(f"Need >=2 files for 70/30 split, got n={n}")

    files = files[:]
    rng.shuffle(files)

    n_train = int(round(0.70 * n))
    n_train = max(1, min(n_train, n - 1))
    return files[:n_train], files[n_train:]


def _build_index(
    files_with_label: List[Tuple[str, int]],
    cfg: Dulieu71HzCfg,
    cache: Dict,
    augment: bool,
) -> List[Tuple[str, int, int, str]]:
    """
    Returns list of (fp, label, start_idx, aug_type)
      aug_type: 'clean', 'noise_K', 'reverse'
    """
    index: List[Tuple[str, int, int, str]] = []

    for fp, y in files_with_label:
        arr = _load_npy_mmap(fp, cache, expected_channels=cfg.channels)
        starts = _starts(int(arr.shape[0]), int(cfg.window), int(cfg.step))

        for s in starts:
            if augment:
                index.append((fp, y, s, "clean"))

                for k in cfg.noise_ks:
                    index.append((fp, y, s, f"noise_{k:.2f}"))

                index.append((fp, y, s, "reverse"))
            else:
                index.append((fp, y, s, "clean"))

    return index


def _mean_std_from_train(train_index: List[Tuple[str, int, int, str]], cfg: Dulieu71HzCfg, cache: Dict):
    sum_c = np.zeros((cfg.channels,), dtype=np.float64)
    sumsq_c = np.zeros((cfg.channels,), dtype=np.float64)
    count = 0

    for fp, _, s, aug_type in train_index:
        if aug_type != "clean":
            continue
        w = _load_window(fp, s, cfg, cache).astype(np.float64)  # (T,C)
        sum_c += w.sum(axis=0)
        sumsq_c += (w * w).sum(axis=0)
        count += w.shape[0]

    mean = sum_c / max(count, 1)
    var = sumsq_c / max(count, 1) - mean * mean
    std = np.sqrt(np.maximum(var, 0.0))

    return mean.astype(np.float32), std.astype(np.float32)


# =========================
# DATASET
# =========================
class Dulieu71HzWindows(Dataset):
    def __init__(self, index, cfg: Dulieu71HzCfg, mean=None, std=None):
        self.index = index  # (fp, y, start, aug_type)
        self.cfg = cfg
        self.mean = mean
        self.std = std
        self._cache: Dict = {}

        if cfg.normalize and (mean is None or std is None):
            raise ValueError("normalize=True requires mean/std computed from TRAIN")

    def __len__(self):
        return len(self.index)

    def __getitem__(self, i):
        fp, y, s, aug_type = self.index[i]
        w = _load_window(fp, s, self.cfg, self._cache)  # (T,C)

        # ---- augmentation ----
        if aug_type.startswith("noise_"):
            k = float(aug_type.split("_", 1)[1])
            noise = np.random.normal(0.0, k * self.std[None, :], size=w.shape).astype(np.float32)
            w = w + noise
        elif aug_type == "reverse":
            w = w[::-1]
        elif aug_type == "clean":
            pass
        else:
            raise ValueError(f"Unknown aug_type: {aug_type}")

        # normalize
        if self.cfg.normalize:
            w = (w - self.mean[None, :]) / (self.std[None, :] + self.cfg.eps)

        # output format
        if self.cfg.return_ct:
            w = w.T  # (C,T)

        return torch.from_numpy(w), torch.tensor(y, dtype=torch.long)


# =========================
# BUILD LOADERS
# =========================
def make_loaders(classes, cfg: Dulieu71HzCfg, batch_size: int = 32, num_workers: int = 0):
    rng = random.Random(cfg.seed)

    if classes is None:
        classes = sorted(
            [d for d in os.listdir(cfg.root) if os.path.isdir(os.path.join(cfg.root, d))]
        )

    tr_files: List[Tuple[str, int]] = []
    va_files: List[Tuple[str, int]] = []
    per_class: Dict[str, Dict[str, int]] = {}

    for y, cls in enumerate(classes):
        files = _list_npy_files(cfg, cls)
        tr, va = _split_files_70_30(files, rng)
        tr_files += [(fp, y) for fp in tr]
        va_files += [(fp, y) for fp in va]
        per_class[cls] = {"files": len(files), "train_files": len(tr), "val_files": len(va)}

    init_cache: Dict = {}
    tr_index = _build_index(tr_files, cfg, init_cache, augment=True)
    va_index = _build_index(va_files, cfg, init_cache, augment=False)

    mean, std = _mean_std_from_train(tr_index, cfg, init_cache) if cfg.normalize else (None, None)
    init_cache.clear()

    tr_ds = Dulieu71HzWindows(tr_index, cfg, mean, std)
    va_ds = Dulieu71HzWindows(va_index, cfg, mean, std)

    tr_loader = DataLoader(
        tr_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    va_loader = DataLoader(
        va_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    meta = {
        "train_files": len(tr_files),
        "val_files": len(va_files),
        "train_samples": len(tr_index),
        "val_samples": len(va_index),
        "per_class": per_class,
        "mean": mean,
        "std": std,
        "noise_ks": list(cfg.noise_ks),
    }

    return tr_loader, va_loader, meta

