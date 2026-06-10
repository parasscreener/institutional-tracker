from datetime import timedelta, datetime
from pathlib import Path

from config.settings import RAW_DIR, LOG_DIR, REPORT_DIR, REPORT_RETENTION_DAYS
from src.utils import setup_logging, get_now_ist

logger = setup_logging("prune_data")

def prune_old_files():
    cutoff = get_now_ist().date() - timedelta(days=REPORT_RETENTION_DAYS)
    deleted = []
    for root in [RAW_DIR, LOG_DIR, REPORT_DIR]:
        for file in Path(root).rglob("*"):
            if file.is_file():
                file_date = datetime.fromtimestamp(file.stat().st_mtime).date()
                if file_date < cutoff:
                    file.unlink(missing_ok=True)
                    deleted.append(str(file))
    logger.info("Deleted %d old files", len(deleted))
    return deleted

if __name__ == "__main__":
    try:
        prune_old_files()
    except Exception:
        logger.exception("prune_data.py failed")
        raise
