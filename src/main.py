from src.scraper import run_scraper
from src.strategy import generate_signals
from src.backtest import run_backtest
from src.prune_data import prune_old_files
from src.notify import send_email
from src.utils import setup_logging

logger = setup_logging("main")

def main():
    run_scraper()
    generate_signals()
    run_backtest()
    prune_old_files()
    send_email()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("main.py failed")
        raise
