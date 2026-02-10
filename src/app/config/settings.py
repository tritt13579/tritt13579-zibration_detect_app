from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "Zibration Detect"
    window_width: int = 1200
    window_height: int = 760
