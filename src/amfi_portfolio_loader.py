import pandas as pd
from pathlib import Path
from config.settings import FUNDS_MASTER_FILE, HOLDINGS_DIR
from src.utils import setup_logging, get_now_ist

logger = setup_logging("amfi_portfolio_loader")


def load_amfi_disclosures() -> pd.DataFrame:
    funds = pd.read_csv(FUNDS_MASTER_FILE)
    amfi_funds = funds.loc[funds["holdings_source_priority"].str.lower() == "amfi"].copy()
    if amfi_funds.empty:
        return pd.DataFrame(columns=[
            "portfolio_date", "scheme_code", "scheme_name", "amc_name",
            "ticker", "stock_name", "shares_held", "holding_pct", "aum", "source_name"
        ])

    sample_path = Path("config/sample_holdings.csv")
    if not sample_path.exists():
        logger.warning("Sample AMFI holdings file not found: %s", sample_path)
        return pd.DataFrame()

    sample = pd.read_csv(sample_path)
    sample["portfolio_date"] = pd.to_datetime(sample["portfolio_date"], errors="coerce")
    sample["shares_held"] = pd.to_numeric(sample["shares_held"], errors="coerce")
    sample["holding_pct"] = pd.to_numeric(sample["holding_pct"], errors="coerce")
    sample["aum"] = pd.to_numeric(sample["aum"], errors="coerce")

    out = []
    for _, row in amfi_funds.iterrows():
        df = sample.copy()
        df["scheme_code"] = str(row["scheme_code"])
        df["scheme_name"] = row["scheme_name"]
        df["amc_name"] = row["amc_name"]
        df["source_name"] = "AMFI"
        out.append(df[[
            "portfolio_date", "scheme_code", "scheme_name", "amc_name",
            "ticker", "stock_name", "shares_held", "holding_pct", "aum", "source_name"
        ]])

    result = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    if not result.empty:
        today = get_now_ist().strftime("%Y%m%d")
        result.to_parquet(HOLDINGS_DIR / f"amfi_holdings_{today}.parquet", index=False)
    return result


if __name__ == "__main__":
    print(load_amfi_disclosures().head())
