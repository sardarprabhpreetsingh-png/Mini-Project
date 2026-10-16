import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Load environment variables from .env in project root or backend
env_project_root = PROJECT_ROOT / ".env"
env_backend = BASE_DIR / ".env"
if env_project_root.exists():
    load_dotenv(dotenv_path=env_project_root, override=True)
elif env_backend.exists():
    load_dotenv(dotenv_path=env_backend, override=True)
else:
    load_dotenv(override=True)

# App Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = (os.getenv("GEMINI_MODEL", "") or "gemini-3.8-flash").strip()
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny").strip()

MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_MB", "25")) * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".aac", ".ogg", ".webm", ".flac", ".mp4"
}

# Default speech metrics targets
DEFAULT_TARGET_WPM_MIN = 130
DEFAULT_TARGET_WPM_MAX = 160
DEFAULT_PAUSE_THRESHOLD_SEC = 0.5

DEFAULT_FILLER_WORDS = [
    "um", "uh", "erm", "er", "hmm", "basically", "actually",
    "literally", "you know", "i mean", "sort of", "kind of",
    "like", "ah", "honestly", "right", "so to speak", "to be honest"
]

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "*"
]
