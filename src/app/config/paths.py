from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = DATA_DIR / "models"
STATE_DIR = DATA_DIR / "state"
MODEL_REGISTRY_PATH = STATE_DIR / "model_registry.json"
APP_STATE_PATH = STATE_DIR / "app_state.json"
STYLES_DIR = SRC_ROOT / "app" / "ui" / "styles"
THEME_PATH = STYLES_DIR / "dark_theme.qss"


def ensure_project_dirs() -> None:
    """Create local storage directories for models and app state."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
