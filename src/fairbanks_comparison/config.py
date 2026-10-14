import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()  # finds .env by walking up from this file; real env vars win
except ImportError:  # python-dotenv is optional; defaults still work
    pass


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


def _list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    return [x.strip() for x in raw.split(",") if x.strip()] if raw else default


# --- site / sources ---------------------------------------------------------
STATION = os.getenv("FC_STATION", "PAFA")
IGRA_STATION = os.getenv("FC_IGRA_STATION", "USM00070261")
LAT = float(os.getenv("FC_LAT", "64.82"))
LON = float(os.getenv("FC_LON", "-147.88"))
AREA = [float(x) for x in _list("FC_AREA", ["66.0", "-149.5", "63.5", "-146.0"])]  # N, W, S, E
LEVELS = _list("FC_LEVELS", [
    "1", "2", "3", "5", "7", "10", "20", "30", "50", "70", "100", "125",
    "150", "175", "200", "225", "250", "300", "350", "400", "450", "500",
    "550", "600", "650", "700", "750", "775", "800", "825", "850", "875",
    "900", "925", "950", "975", "1000"])

# --- behavior ---------------------------------------------------------------
USE_IGRA_CACHE = _bool("FC_USE_IGRA_CACHE", False)
HOURS = tuple(int(h) for h in _list("FC_HOURS", ["0", "12"]))

# --- paths ------------------------------------------------------------------
DATA_DIR = Path(os.getenv("FC_DATA_DIR", "data"))
PROFILE_DIR = DATA_DIR / "profiles"
IMG_DIR = DATA_DIR / "img"
HERBIE_DIR = DATA_DIR / "herbie"
IGRA_DIR = DATA_DIR / "igra2"
ERA5_DIR = DATA_DIR / "era5"
RADIO_DIR = DATA_DIR / "radio"
REPORT_DIR = DATA_DIR / "reports"

for _d in (DATA_DIR, PROFILE_DIR, IMG_DIR, HERBIE_DIR, IGRA_DIR, ERA5_DIR, RADIO_DIR, REPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)