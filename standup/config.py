import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

STANDUP_DIR = Path.home() / ".standup"
DB_PATH = STANDUP_DIR / "standup.db"

ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-6"


def ensure_dir() -> None:
    STANDUP_DIR.mkdir(parents=True, exist_ok=True)
