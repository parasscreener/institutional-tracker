import pandas as pd
import requests
from io import StringIO
from pathlib import Path
from config.settings import FUNDS_MASTER_FILE, HOLDINGS_DIR
from src.utils import setup_logging, get_now_ist

logger = setup_logging("amc_disclosure_loader")


def _load_csv(source: str) -> pd.DataFrame:
    if source.startswith("http"):
        r = requests.get(source, timeout=30)
        r.raise_for_status()
        return pd.read_csv(StringIO(r.text))
    return pd.read_csv(source)


def _load_json(source: str) -> pd.DataFrame:
    if source.startswith("http"):
        r = requests.get(source, timeout=30)
        r.raise_for_status()
        payload = r.json()
    else:
        import json
        payload = json.loads(Path(source).read_text(encoding='utf-8'))
    records = payload.get("data", payload if isinstance(payload, list) else [])
    return pd.DataFrame(records)


def load_amc_disclosures() -> pd.DataFrame:
    funds = pd.read_csv(FUNDS_MASTER_FILE)
    amc_funds = funds.loc[funds["holdings_source_priority"].str.lower() == "amc"].copy()
    if amc_funds.empty:
        return pd.DataFrame(columns=[
            "portfolio_date", "scheme_code", "scheme_name", "amc_name",
            "ticker", "stock_name", "shares_held", "holding_pct", "aum", "source_name"
        ])

    frames = []
    for _, row in amc_funds.iterrows():
        source = str(row.get("amc_holdings_url", "")).strip()
        fmt = str(row.get("amc_holdings_format", "csv")).strip().lower()
        if not source:
            continue
        try:
            df = _load_json(source) if fmt == 'json' else _load_csv(source)
            rename_map = {
                'stock': 'ticker', 'company_name': 'stock_name', 'security_name': 'stock_name',
                'quantity': 'shares_held', 'shares': 'shares_held', 'disclosure_date': 'portfolio_date'
            }
            df = df.rename(columns={c: rename_map[c] for c in df.columns if c in rename_map})
            if 'portfolio_date' not in df.columns:
                df['portfolio_date'] = get_now_ist().date().isoformat()
            if 'holding_pct' not in df.columns:
                df['holding_pct'] = pd.NA
            if 'aum' not in df.columns:
                df['aum'] = pd.NA
            df['portfolio_date'] = pd.to_datetime(df['portfolio_date'], errors='coerce')
            df['shares_held'] = pd.to_numeric(df['shares_held'], errors='coerce')
            df['holding_pct'] = pd.to_numeric(df['holding_pct'], errors='coerce')
            df['scheme_code'] = str(row['scheme_code'])
            df['scheme_name'] = row['scheme_name']
            df['amc_name'] = row['amc_name']
            df['source_name'] = 'AMC'
            frames.append(df[[
                'portfolio_date', 'scheme_code', 'scheme_name', 'amc_name',
                'ticker', 'stock_name', 'shares_held', 'holding_pct', 'aum', 'source_name'
            ]].dropna(subset=['portfolio_date', 'ticker']))
        except Exception:
            logger.exception('Failed to load AMC disclosure for scheme_code=%s', row['scheme_code'])

    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not result.empty:
        today = get_now_ist().strftime('%Y%m%d')
        result.to_parquet(HOLDINGS_DIR / f"amc_holdings_{today}.parquet", index=False)
    return result


if __name__ == '__main__':
    print(load_amc_disclosures().head())
