# train_cnn1d_dulieu71Hz_file_70_30.py
import os

os.environ["PYTHONHASHSEED"] = "4"
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":16:8")

import json
import random

import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn

from dulieu71Hz_file_split_70_30 import Dulieu71HzCfg, make_loaders


# =========================
# CONFIG
# =========================
CFG_USE_AMP = False  # AMP only on CUDA
GLOBAL_SEED = 4
SPLIT_SEED = 42

DATASET_ROOT = "./Dulieu/dulieu71Hz"
DATASET_CHANNELS = 3
WINDOW = 2048
STEP = 2048

HISTORY_DIR = "./History_Dulieu71Hz"


# =========================
# UTIL
# =========================
def set_global_determinism(seed: int = 4):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)


def _counts(arr: np.ndarray):
    d = {}
    for v in arr.tolist():
        d[int(v)] = d.get(int(v), 0) + 1
    return dict(sorted(d.items(), key=lambda x: x[0]))


def make_versioned_run_dir(base_dir: str, prefix: str = "v"):
    os.makedirs(base_dir, exist_ok=True)

    existing = []
    for name in os.listdir(base_dir):
        if name.startswith(prefix):
            num_part = name[len(prefix) :]
            if num_part.isdigit():
                existing.append(int(num_part))

    next_v = (max(existing) + 1) if existing else 1
    version = f"{prefix}{next_v}"
    run_dir = os.path.join(base_dir, version)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir, version


def plot_history(history, out_base_png):
    epochs = np.arange(1, len(history["loss"]) + 1)

    plt.figure()
    plt.plot(epochs, history["loss"], label="train_loss")
    plt.plot(epochs, history["val_loss"], label="val_loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_base_png.replace(".png", "_loss.png"), dpi=160)
    plt.close()

    plt.figure()
    plt.plot(epochs, history["acc"], label="train_acc")
    plt.plot(epochs, history["val_acc"], label="val_acc")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_base_png.replace(".png", "_acc.png"), dpi=160)
    plt.close()


def plot_confusion_matrix(y_true, y_pred, num_classes, out_path_png, title="Confusion Matrix"):
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        cm[int(t), int(p)] += 1

    plt.figure()
    plt.imshow(cm)
    plt.title(title)
    plt.xlabel("Pred")
    plt.ylabel("True")
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(out_path_png, dpi=160)
    plt.close()


def _to_list_float(x):
    if x is None:
        return None
    return np.asarray(x, dtype=np.float32).tolist()


def _build_checkpoint_payload(
    model,
    classes,
    cfg,
    meta,
    best_epoch,
    best_val_loss,
    history,
    base_filters,
    dropout,
    weight_decay,
    use_amp,
):
    mean = _to_list_float(meta.get("mean"))
    std = _to_list_float(meta.get("std"))

    if mean is None or std is None:
        raise ValueError("Checkpoint requires normalization parameters: meta.mean/meta.std")
    if len(mean) != int(cfg.channels) or len(std) != int(cfg.channels):
        raise ValueError(
            f"Normalization shape mismatch: len(mean)={len(mean)}, len(std)={len(std)}, channels={cfg.channels}"
        )

    meta_out = dict(meta)
    meta_out["mean"] = mean
    meta_out["std"] = std

    payload = {
        "checkpoint_format": "zibration_detect_app_cnn1d_v1",
        "model_state_dict": model.state_dict(),
        "classes": list(classes),
        "cfg": dict(cfg.__dict__),
        "meta": meta_out,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "history": history,
        "cnn1d_params": {
            "base_filters": base_filters,
            "dropout": dropout,
            "weight_decay": weight_decay,
            "use_amp": use_amp,
        },
        # Convenience mirrors for legacy/fallback readers.
        "mean": mean,
        "std": std,
    }
    return payload


@torch.no_grad()
def eval_loop(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    all_true = []
    all_pred = []

    for xb, yb in loader:
        xb = xb.to(device, non_blocking=True)
        yb = yb.to(device, non_blocking=True)

        logits = model(xb)
        loss = criterion(logits, yb)

        total_loss += loss.item() * xb.size(0)
        pred = logits.argmax(dim=1)
        correct += (pred == yb).sum().item()
        total += xb.size(0)

        all_true.append(yb.detach().cpu().numpy())
        all_pred.append(pred.detach().cpu().numpy())

    all_true = np.concatenate(all_true) if all_true else np.array([], dtype=np.int64)
    all_pred = np.concatenate(all_pred) if all_pred else np.array([], dtype=np.int64)

    avg_loss = total_loss / max(total, 1)
    acc = correct / max(total, 1)
    return avg_loss, acc, all_true, all_pred


# =========================
# MODEL: Simple 1D CNN
# =========================
class SimpleCNN1D(nn.Module):
    def __init__(self, num_classes: int, input_channels: int, base_filters: int = 32, dropout: float = 0.5):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv1d(input_channels, base_filters, kernel_size=7, stride=1, padding=3),
            nn.BatchNorm1d(base_filters),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
            nn.Conv1d(base_filters, base_filters * 2, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm1d(base_filters * 2),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
            nn.Conv1d(base_filters * 2, base_filters * 4, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(base_filters * 4),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
            nn.Conv1d(base_filters * 4, base_filters * 8, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(base_filters * 8),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
        )

        self.gap = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(base_filters * 8, base_filters * 4),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(base_filters * 4, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.gap(x).squeeze(-1)
        return self.fc(x)


def train_cnn1d_file_split_70_30(
    classes=None,
    batch_size: int = 32,
    epochs: int = 30,
    learning_rate: float = 5e-4,
    base_filters: int = 64,
    dropout: float = 0.4,
    weight_decay: float = 1e-4,
    num_workers: int = 4,
):
    set_global_determinism(GLOBAL_SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[MAIN] Device: {device}")

    run_dir, version = make_versioned_run_dir(HISTORY_DIR, prefix="v")
    print(f"[MAIN] Output: {run_dir}")

    cfg = Dulieu71HzCfg(
        root=DATASET_ROOT,
        channels=DATASET_CHANNELS,
        window=WINDOW,
        step=STEP,
        seed=SPLIT_SEED,
        normalize=True,
        return_ct=True,
        noise_ks=(0.03, 0.05, 0.07),
    )

    if classes is None:
        classes = sorted([d for d in os.listdir(cfg.root) if os.path.isdir(os.path.join(cfg.root, d))])
    print(f"[DATA] Classes: {classes}")

    train_loader, val_loader, meta = make_loaders(
        classes=classes,
        cfg=cfg,
        batch_size=batch_size,
        num_workers=num_workers,
    )
    print(f"[DATA] Train samples: {meta['train_samples']} | Val samples: {meta['val_samples']}")

    if meta.get("mean") is None or meta.get("std") is None:
        raise ValueError("Data loader did not return normalization parameters mean/std.")

    model = SimpleCNN1D(
        num_classes=len(classes),
        input_channels=cfg.channels,
        base_filters=base_filters,
        dropout=dropout,
    ).to(device)

    use_amp = bool(CFG_USE_AMP and (device.type == "cuda"))
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    criterion = nn.CrossEntropyLoss()
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5, patience=5)
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    history = {"loss": [], "acc": [], "val_loss": [], "val_acc": []}
    best_val_loss = float("inf")
    best_epoch = -1
    ckpt_path = os.path.join(run_dir, f"cnn1d_dulieu71Hz_file_70_30_best_{version}.pt")

    last_val_true = None
    last_val_pred = None

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        train_true_all = []
        train_pred_all = []

        for xb, yb in train_loader:
            xb = xb.to(device, non_blocking=True)
            yb = yb.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)

            if use_amp:
                with torch.cuda.amp.autocast():
                    logits = model(xb)
                    loss = criterion(logits, yb)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                logits = model(xb)
                loss = criterion(logits, yb)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

            total_loss += loss.item() * xb.size(0)
            pred = logits.argmax(dim=1)
            correct += (pred == yb).sum().item()
            total += xb.size(0)

            train_true_all.append(yb.detach().cpu().numpy())
            train_pred_all.append(pred.detach().cpu().numpy())

        train_loss = total_loss / max(total, 1)
        train_acc = correct / max(total, 1)

        train_true_all = np.concatenate(train_true_all) if train_true_all else np.array([], dtype=np.int64)
        train_pred_all = np.concatenate(train_pred_all) if train_pred_all else np.array([], dtype=np.int64)

        val_loss, val_acc, val_true, val_pred = eval_loop(model, val_loader, criterion, device)
        last_val_true, last_val_pred = val_true, val_pred

        history["loss"].append(train_loss)
        history["acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        print(
            f"Epoch {epoch:03d}/{epochs} "
            f"- loss:{train_loss:.4f} acc:{train_acc:.4f} "
            f"- val_loss:{val_loss:.4f} val_acc:{val_acc:.4f}"
        )
        print(f"[TRAIN] y_true counts: {_counts(train_true_all)}")
        print(f"[TRAIN] y_pred counts: {_counts(train_pred_all)}")
        print(f"[VAL]   y_true counts: {_counts(val_true)}")
        print(f"[VAL]   y_pred counts: {_counts(val_pred)}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            checkpoint_payload = _build_checkpoint_payload(
                model=model,
                classes=classes,
                cfg=cfg,
                meta=meta,
                best_epoch=best_epoch,
                best_val_loss=best_val_loss,
                history=history,
                base_filters=base_filters,
                dropout=dropout,
                weight_decay=weight_decay,
                use_amp=use_amp,
            )
            torch.save(
                checkpoint_payload,
                ckpt_path,
            )
            print(f"[CKPT] Saved best -> {ckpt_path} (epoch={best_epoch}, val_loss={best_val_loss:.4f})")

        scheduler.step(val_loss)

    with open(
        os.path.join(run_dir, f"cnn1d_dulieu71Hz_file_70_30_history_{version}.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    plot_history(history, os.path.join(run_dir, f"cnn1d_dulieu71Hz_file_70_30_curves_{version}.png"))

    if last_val_true is not None and last_val_pred is not None:
        plot_confusion_matrix(
            last_val_true,
            last_val_pred,
            len(classes),
            os.path.join(run_dir, f"cnn1d_dulieu71Hz_file_70_30_val_cm_{version}.png"),
            title=f"VAL Confusion Matrix (CNN1D 70/30 file split) - {version}",
        )

    print(f"[DONE] best_epoch={best_epoch}, best_val_loss={best_val_loss:.4f}")
    print(f"[SAVED] {run_dir} (history + plots + ckpt)")
    return model, history


if __name__ == "__main__":
    train_cnn1d_file_split_70_30(
        classes=None,
        batch_size=32,
        epochs=30,
        learning_rate=5e-4,
        base_filters=64,
        dropout=0.4,
        weight_decay=1e-4,
        num_workers=4,
    )

