import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import FUNDS_MASTER_FILE, NAV_DIR, LATEST_HOLDINGS_FILE
from src.utils import setup_logging, ensure_dirs, get_now_ist, save_parquet
from src.amfi_portfolio_loader import load_amfi_disclosures
from src.amc_disclosure_loader import load_amc_disclosures

logger = setup_logging("scraper")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_json(url: str):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def load_funds_master() -> pd.DataFrame:
    return pd.read_csv(FUNDS_MASTER_FILE)

def fetch_nav_history(scheme_code: str) -> pd.DataFrame:
    payload = get_json(f"https://api.mfapi.in/mf/{scheme_code}")
    data = payload.get("data", [])
    meta = payload.get("meta", {})
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame()
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
    df['scheme_code'] = scheme_code
    df['scheme_name'] = meta.get('scheme_name')
    df['amc_name'] = meta.get('fund_house')
    return df.dropna(subset=['date', 'nav']).sort_values('date')

def run_scraper() -> pd.DataFrame:
    ensure_dirs()
    funds = load_funds_master()
    today = get_now_ist().strftime('%Y%m%d')

    for _, row in funds.iterrows():
        try:
            nav_df = fetch_nav_history(str(row['scheme_code']))
            if not nav_df.empty:
                nav_df.to_parquet(NAV_DIR / f"nav_{row['scheme_code']}_{today}.parquet", index=False)
        except Exception:
            logger.exception('Failed NAV fetch for scheme_code=%s', row['scheme_code'])

    amfi_df = load_amfi_disclosures()
    amc_df = load_amc_disclosures()
    latest = pd.concat([df for df in [amfi_df, amc_df] if not df.empty], ignore_index=True) if (not amfi_df.empty or not amc_df.empty) else pd.DataFrame(columns=[
        'portfolio_date', 'scheme_code', 'scheme_name', 'amc_name',
        'ticker', 'stock_name', 'shares_held', 'holding_pct', 'aum', 'source_name'
    ])
    save_parquet(latest, LATEST_HOLDINGS_FILE)
    return latest

if __name__ == '__main__':
    try:
        run_scraper()
    except Exception:
        logger.exception('scraper.py failed')
        raise
