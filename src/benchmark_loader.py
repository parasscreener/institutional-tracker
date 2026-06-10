import pandas as pd
from config.settings import BENCHMARK_FILE
from src.utils import setup_logging

logger = setup_logging("benchmark_loader")

def create_sample_benchmark() -> None:
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=4000)
    rets = pd.Series(0.00035, index=dates)
    prices = 1000 * (1 + rets).cumprod()
    df = pd.DataFrame({"date": dates, "close": prices.values})
    df.to_csv(BENCHMARK_FILE, index=False)
    logger.info("Created sample benchmark at %s", BENCHMARK_FILE)

if __name__ == "__main__":
    create_sample_benchmark()
