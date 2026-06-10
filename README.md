# Institutional Tracker on GitHub

A serverless GitHub Actions pipeline for tracking mutual fund entry/exit signals, running a daily rolling 15-year vectorized backtest, pruning repository data older than 180 days, and emailing an HTML report.

## Upgraded data architecture

This version separates data into three layers:

- NAV history from `mfapi.in`
- AMFI portfolio disclosures as the preferred holdings source
- AMC-hosted CSV/JSON disclosure files as fallback or enrichment

The signal engine also assigns a confidence score:

- High: quantity-based accumulation or reduction
- Medium: allocation-weight style inference where quantity evidence is weaker
- Low: weak or incomplete evidence

## What this repository does

- Pulls mutual fund NAV history from `mfapi.in`
- Loads holdings from AMFI or AMC disclosure files
- Detects institutional actions using:
  - Entry: accumulation by at least 3 funds within 30 days
  - Exit: liquidation or reduction greater than 25% of previous shares held
- Runs a daily 15-year rolling backtest and compares against Nifty 50 TR Index
- Deletes raw/log/report files older than 180 days before committing changes
- Emails a flat HTML table report through Gmail SMTP
- Adds disclosure date, data-source labels, and confidence notes to the report

## Required secrets

- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`

## Quick start

1. Create a new GitHub repository.
2. Copy these files into the root.
3. Update `config/funds_master.csv` with your real scheme codes and AMFI/AMC disclosure sources.
4. Replace the sample benchmark generator with a real Nifty 50 TR source.
5. Add Gmail secrets in repository settings.
6. Run `workflow_dispatch` once to validate.

## Updated holdings config

`config/funds_master.csv` now supports:

- `holdings_source_priority`: `amfi` or `amc`
- `amfi_disclosure_id`: optional AMFI mapping field
- `amc_holdings_url`: CSV/JSON/local path
- `amc_holdings_format`: `csv` or `json`

## Important note

Public mutual fund holdings are generally periodic disclosures, not true daily transaction feeds. The GitHub workflow can run daily, but holdings-based institutional signals should be interpreted as updates from the latest available disclosure date.
