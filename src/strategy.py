import numpy as np
import pandas as pd

from config.settings import (
    LATEST_HOLDINGS_FILE, PREVIOUS_HOLDINGS_FILE, SIGNALS_FILE,
    ENTRY_MIN_FUNDS, ENTRY_LOOKBACK_DAYS, EXIT_REDUCTION_THRESHOLD
)
from src.utils import setup_logging, save_csv
from src.signal_confidence import assign_confidence

logger = setup_logging("strategy")

def load_parquet_safe(path):
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()

def generate_signals() -> pd.DataFrame:
    latest = load_parquet_safe(LATEST_HOLDINGS_FILE)
    prev = load_parquet_safe(PREVIOUS_HOLDINGS_FILE)

    if latest.empty:
        result = pd.DataFrame(columns=[
            'stock_name', 'ticker', 'amc_name', 'action_type', 'current_position',
            'change_pct', 'transaction_volume', 'portfolio_date', 'source_name', 'confidence'
        ])
        save_csv(result, SIGNALS_FILE)
        return result

    prev_small = prev[[c for c in ['scheme_code', 'ticker', 'shares_held', 'holding_pct'] if c in prev.columns]].copy() if not prev.empty else pd.DataFrame(columns=['scheme_code', 'ticker', 'shares_held', 'holding_pct'])
    prev_small = prev_small.rename(columns={'shares_held': 'prev_shares_held', 'holding_pct': 'prev_holding_pct'})

    compare = latest.merge(prev_small, on=['scheme_code', 'ticker'], how='left')
    compare['prev_shares_held'] = compare['prev_shares_held'].fillna(0)
    compare['prev_holding_pct'] = compare['prev_holding_pct'].fillna(0)

    compare['change_shares'] = compare['shares_held'].fillna(0) - compare['prev_shares_held']
    compare['change_pct'] = np.where(
        compare['prev_shares_held'] > 0,
        compare['change_shares'] / compare['prev_shares_held'] * 100,
        np.where(compare['shares_held'].fillna(0) > 0, 100.0, (compare['holding_pct'].fillna(0) - compare['prev_holding_pct']) * 100)
    )

    compare['action_type'] = np.select(
        [
            (compare['prev_shares_held'] == 0) & (compare['shares_held'].fillna(0) > 0),
            (compare['prev_shares_held'] > 0) & (compare['shares_held'].fillna(0) == 0),
            (compare['change_pct'] > 0),
            (compare['change_pct'] <= EXIT_REDUCTION_THRESHOLD),
        ],
        ['Entry', 'Exit', 'Accumulation', 'Reduction'],
        default='Hold'
    )

    compare['transaction_volume'] = compare['change_shares'].abs()
    compare['portfolio_date'] = pd.to_datetime(compare['portfolio_date'])
    latest_date = compare['portfolio_date'].max()
    recent = compare.loc[compare['portfolio_date'] >= latest_date - pd.Timedelta(days=ENTRY_LOOKBACK_DAYS)].copy()

    counts = (
        recent.loc[recent['action_type'].isin(['Entry', 'Accumulation'])]
        .groupby('ticker')['scheme_code'].nunique().rename('fund_count').reset_index()
    )
    qualified = set(counts.loc[counts['fund_count'] >= ENTRY_MIN_FUNDS, 'ticker'])

    result = compare.loc[
        ((compare['ticker'].isin(qualified)) & (compare['action_type'].isin(['Entry', 'Accumulation']))) |
        (compare['action_type'].isin(['Exit', 'Reduction']))
    ].copy()

    result['current_position'] = result['shares_held'].round(2)
    result['change_pct'] = result['change_pct'].round(2)
    result['transaction_volume'] = result['transaction_volume'].round(2)
    result = assign_confidence(result)

    result = result[[
        'stock_name', 'ticker', 'amc_name', 'action_type', 'current_position', 'change_pct',
        'transaction_volume', 'portfolio_date', 'source_name', 'confidence'
    ]].sort_values(['confidence', 'action_type', 'ticker', 'amc_name'])

    save_csv(result, SIGNALS_FILE)
    latest.to_parquet(PREVIOUS_HOLDINGS_FILE, index=False)
    return result

if __name__ == '__main__':
    try:
        generate_signals()
    except Exception:
        logger.exception('strategy.py failed')
        raise
