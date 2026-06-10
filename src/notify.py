import os
import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import SIGNALS_FILE, BACKTEST_FILE, TARGET_EMAIL, GMAIL_SMTP_HOST, GMAIL_SMTP_PORT
from src.utils import setup_logging, get_now_ist, read_json

logger = setup_logging("notify")


def esc(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def build_html_table(df: pd.DataFrame) -> str:
    if df.empty:
        return '<p>No stocks met the threshold today.</p>'
    rows = []
    for _, r in df.iterrows():
        rows.append(
            '<tr>'
            f"<td>{esc(r['stock_name'])} / {esc(r['ticker'])}</td>"
            f"<td>{esc(r['amc_name'])}</td>"
            f"<td>{esc(r['action_type'])}</td>"
            f"<td>{esc(r['current_position'])}</td>"
            f"<td>{esc(r['change_pct'])}</td>"
            f"<td>{esc(r['transaction_volume'])}</td>"
            '</tr>'
        )
    return """
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:14px;">
      <thead style="background:#f2f2f2;">
        <tr>
          <th align="left">Stock / Ticker</th>
          <th align="left">AMC Name</th>
          <th align="left">Action Type (Entry/Exit/Accumulation/Reduction)</th>
          <th align="left">Current Position</th>
          <th align="left">Change %</th>
          <th align="left">Transaction Volume</th>
        </tr>
      </thead>
      <tbody>%s</tbody>
    </table>
    """ % ''.join(rows)


def build_signal_notes(df: pd.DataFrame) -> str:
    if df.empty:
        return ''
    disclosure_date = pd.to_datetime(df['portfolio_date']).max().date()
    confidence_mix = ', '.join(f"{k}: {v}" for k, v in df['confidence'].value_counts().to_dict().items()) if 'confidence' in df.columns else 'N/A'
    sources = ', '.join(sorted(df['source_name'].dropna().astype(str).unique())) if 'source_name' in df.columns else 'N/A'
    return f"<p><b>Latest disclosure date:</b> {disclosure_date} | <b>Sources:</b> {sources} | <b>Confidence mix:</b> {confidence_mix}</p>"


def build_footer(metrics: dict) -> str:
    s = metrics.get('strategy', {})
    b = metrics.get('benchmark', {})
    return f"""
    <h3>15-Year Rolling Backtest</h3>
    <p><b>Strategy</b> — CAGR: {s.get('CAGR')}, Sharpe: {s.get('Sharpe')}, MDD: {s.get('MDD')}, Sortino: {s.get('Sortino')}</p>
    <p><b>{b.get('name', 'Benchmark')}</b> — CAGR: {b.get('CAGR')}, Sharpe: {b.get('Sharpe')}, MDD: {b.get('MDD')}, Sortino: {b.get('Sortino')}</p>
    """


def send_email() -> None:
    gmail_user = os.environ['GMAIL_USER']
    gmail_password = os.environ['GMAIL_APP_PASSWORD']
    df = pd.read_csv(SIGNALS_FILE) if SIGNALS_FILE.exists() else pd.DataFrame(columns=[
        'stock_name', 'ticker', 'amc_name', 'action_type', 'current_position', 'change_pct', 'transaction_volume', 'portfolio_date', 'source_name', 'confidence'
    ])
    metrics = read_json(BACKTEST_FILE, default={})
    today_str = get_now_ist().strftime('%Y-%m-%d')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Institutional Tracker Daily Report - {today_str}'
    msg['From'] = gmail_user
    msg['To'] = TARGET_EMAIL

    html = f"""
    <html><body>
      <h2>Institutional Entry/Exit Report - {today_str}</h2>
      <p>Daily orchestration run. Institutional signals are based on the most recently disclosed portfolio snapshot, not necessarily same-day fund trading.</p>
      {build_signal_notes(df)}
      {build_html_table(df)}
      <br/>
      {build_footer(metrics)}
    </body></html>
    """
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, [TARGET_EMAIL], msg.as_string())

    logger.info('Email sent successfully to %s', TARGET_EMAIL)


if __name__ == '__main__':
    try:
        send_email()
    except Exception:
        logger.exception('notify.py failed')
        raise
