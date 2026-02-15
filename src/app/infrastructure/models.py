"""1D CNN model architecture for vibration detection."""
from __future__ import annotations

import torch
from torch import nn


class SimpleCNN1D(nn.Module):
    """Simple 1D CNN for vibration signal classification.
    
    This architecture matches the model used in train_cnn1d_dulieu71Hz_file_70_30.py.
    """

    def __init__(
        self,
        num_classes: int,
        input_channels: int,
        base_filters: int = 32,
        dropout: float = 0.5,
    ) -> None:
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

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.gap(x).squeeze(-1)
        return self.fc(x)
