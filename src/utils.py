import json
import logging
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

from config.settings import (
    TZ, RAW_DIR, NAV_DIR, HOLDINGS_DIR, ASSETS_DIR,
    PROCESSED_DIR, STATE_DIR, LOG_DIR, REPORT_DIR
)

def ensure_dirs() -> None:
    for path in [RAW_DIR, NAV_DIR, HOLDINGS_DIR, ASSETS_DIR, PROCESSED_DIR, STATE_DIR, LOG_DIR, REPORT_DIR]:
        path.mkdir(parents=True, exist_ok=True)

def get_now_ist() -> datetime:
    return datetime.now(ZoneInfo(TZ))

def setup_logging(name: str) -> logging.Logger:
    ensure_dirs()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    ts = get_now_ist().strftime("%Y%m%d")
    log_file = LOG_DIR / f"{name}_{ts}.log"
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger

def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

def read_json(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

def save_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
