from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_DIR = DATA_DIR / "state"
LOG_DIR = BASE_DIR / "logs" / "daily"
REPORT_DIR = BASE_DIR / "reports" / "daily"

NAV_DIR = RAW_DIR / "nav"
HOLDINGS_DIR = RAW_DIR / "holdings"
ASSETS_DIR = RAW_DIR / "assets"

FUNDS_MASTER_FILE = BASE_DIR / "config" / "funds_master.csv"
BENCHMARK_FILE = PROCESSED_DIR / "nifty50tr.csv"

LATEST_HOLDINGS_FILE = PROCESSED_DIR / "latest_holdings.parquet"
PREVIOUS_HOLDINGS_FILE = STATE_DIR / "previous_holdings.parquet"
SIGNALS_FILE = PROCESSED_DIR / "signals_latest.csv"
BACKTEST_FILE = PROCESSED_DIR / "backtest_metrics.json"
TRACKED_POSITIONS_FILE = STATE_DIR / "tracked_positions.json"

TZ = "Asia/Kolkata"
REPORT_RETENTION_DAYS = 180
ROLLING_BACKTEST_YEARS = 15
ENTRY_MIN_FUNDS = 3
ENTRY_LOOKBACK_DAYS = 30
EXIT_REDUCTION_THRESHOLD = -25.0
TARGET_EMAIL = "paras.m.parmar@gmail.com"

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587
