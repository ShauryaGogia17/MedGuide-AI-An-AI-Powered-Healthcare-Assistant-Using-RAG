"""Configuration resolved from the repository root, independent of cwd."""
import os
from pathlib import Path
from threading import Lock
from dotenv import dotenv_values, load_dotenv

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
_PROVIDER_SETTINGS = frozenset({"OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_EMBEDDING_MODEL"})
_inherited_dotenv_settings = _PROVIDER_SETTINGS.intersection(
    os.getenv('MEDGUIDE_DOTENV_PROVIDER_SETTINGS', '').split(',')
)
# Process-level configuration keeps precedence over the development .env file.
_external_provider_settings = _PROVIDER_SETTINGS.intersection(os.environ) - _inherited_dotenv_settings
load_dotenv(ENV_FILE)
# The development launcher imports .env before spawning us. Its inherited file
# values may be stale when Uvicorn restarts a child, so reread those marked keys.
if _inherited_dotenv_settings:
    _startup_values = dotenv_values(ENV_FILE)
    for _name in _inherited_dotenv_settings:
        _value = _startup_values.get(_name)
        if _value is None:
            os.environ.pop(_name, None)
        else:
            os.environ[_name] = _value

def _env_fingerprint():
    try:
        stat = ENV_FILE.stat()
        return stat.st_mtime_ns, stat.st_size
    except FileNotFoundError:
        return None

_provider_env_fingerprint = _env_fingerprint()
_provider_config_lock = Lock()

def refresh_provider_config():
    """Pick up saved provider settings without restarting the running service."""
    global _provider_env_fingerprint
    fingerprint = _env_fingerprint()
    if fingerprint == _provider_env_fingerprint:
        return
    with _provider_config_lock:
        fingerprint = _env_fingerprint()
        if fingerprint == _provider_env_fingerprint:
            return
        values = dotenv_values(ENV_FILE) if fingerprint is not None else {}
        for name in _PROVIDER_SETTINGS - _external_provider_settings:
            value = values.get(name)
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        _provider_env_fingerprint = fingerprint

def root_path(name: str, default: str) -> Path:
    path = Path(os.getenv(name, default)).expanduser()
    return path if path.is_absolute() else ROOT / path

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
UPLOAD_DIR = root_path("UPLOAD_DIR", "uploads/reports")
VECTOR_DB_PATH = root_path("VECTOR_DB_PATH", "vector_db")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
