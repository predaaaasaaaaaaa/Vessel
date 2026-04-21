import os
import json
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".vessel"
CONFIG_FILE = CONFIG_DIR / "config.json"

def get_config() -> dict:
    """Reads the Vessel configuration from ~/.vessel/config.json."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(config: dict) -> None:
    """Saves the Vessel configuration."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_api_key() -> Optional[str]:
    """Helper to retrieve the OpenAI API key."""
    # First check environment variable, then config file
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        return env_key
    return get_config().get("openai_api_key")
