import numpy as np
import pandas as pd

from config.settings import BACKTEST_FILE, NAV_DIR, BENCHMARK_FILE, ROLLING_BACKTEST_YEARS
from src.utils import setup_logging, write_json

logger = setup_logging("backtest")

def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    returns = returns.dropna()
    if returns.empty:
        return 0.0
    total = (1 + returns).prod()
    years = len(returns) / periods_per_year
    return float(total ** (1 / years) - 1) if years > 0 else 0.0

def sharpe_ratio(returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    excess = returns.dropna() - rf / periods_per_year
    vol = excess.std(ddof=0)
    return float((excess.mean() / vol) * np.sqrt(periods_per_year)) if vol > 0 else 0.0

def sortino_ratio(returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    excess = returns.dropna() - rf / periods_per_year
    downside = excess[excess < 0].std(ddof=0)
    return float((excess.mean() / downside) * np.sqrt(periods_per_year)) if downside is not None and downside > 0 else 0.0

def max_drawdown(equity_curve: pd.Series) -> float:
    dd = equity_curve / equity_curve.cummax() - 1.0
    return float(dd.min()) if not dd.empty else 0.0

def load_nav_panel() -> pd.DataFrame:
    files = sorted(NAV_DIR.glob("nav_*.parquet"))
    if not files:
        raise FileNotFoundError("No NAV parquet files found in data/raw/nav")
    frames = [pd.read_parquet(f)[["date", "scheme_code", "nav"]] for f in files]
    df = pd.concat(frames, ignore_index=True).drop_duplicates(["date", "scheme_code"], keep="last")
    df["date"] = pd.to_datetime(df["date"])
    return df.pivot(index="date", columns="scheme_code", values="nav").sort_index()

def load_benchmark() -> pd.Series:
    if not BENCHMARK_FILE.exists():
        raise FileNotFoundError(f"Benchmark file missing: {BENCHMARK_FILE}")
    df = pd.read_csv(BENCHMARK_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df.set_index("date")["close"].sort_index().dropna()

def build_strategy_returns(nav_panel: pd.DataFrame) -> pd.Series:
    daily_ret = nav_panel.pct_change().replace([np.inf, -np.inf], np.nan)
    momentum = nav_panel.pct_change(126)
    signal = (momentum.rank(axis=1, pct=True) >= 0.7).astype(float).shift(1)
    weights = signal.div(signal.sum(axis=1), axis=0).fillna(0)
    return (weights * daily_ret).sum(axis=1).fillna(0)

def run_backtest() -> dict:
    nav_panel = load_nav_panel()
    cutoff = nav_panel.index.max() - pd.DateOffset(years=ROLLING_BACKTEST_YEARS)
    nav_panel = nav_panel.loc[nav_panel.index >= cutoff].copy()

    strategy_ret = build_strategy_returns(nav_panel)
    benchmark_ret = load_benchmark().pct_change().reindex(strategy_ret.index).fillna(0)

    strategy_eq = (1 + strategy_ret).cumprod()
    benchmark_eq = (1 + benchmark_ret).cumprod()

    result = {
        "window_years": ROLLING_BACKTEST_YEARS,
        "as_of_date": str(strategy_ret.index.max().date()),
        "strategy": {
            "CAGR": round(annualized_return(strategy_ret), 6),
            "Sharpe": round(sharpe_ratio(strategy_ret), 6),
            "MDD": round(max_drawdown(strategy_eq), 6),
            "Sortino": round(sortino_ratio(strategy_ret), 6),
        },
        "benchmark": {
            "name": "Nifty 50 TR Index",
            "CAGR": round(annualized_return(benchmark_ret), 6),
            "Sharpe": round(sharpe_ratio(benchmark_ret), 6),
            "MDD": round(max_drawdown(benchmark_eq), 6),
            "Sortino": round(sortino_ratio(benchmark_ret), 6),
        },
    }
    write_json(BACKTEST_FILE, result)
    return result

if __name__ == "__main__":
    try:
        logger.info(run_backtest())
    except Exception:
        logger.exception("backtest.py failed")
        raise
