import pandas as pd
from pathlib import Path
import os
from datetime import datetime
import schedule
import time

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "market_data.db"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_alert(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[Alert - no Telegram configured] {message}")
        return
    
    import requests
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Failed to send alert: {e}")

def monitor_signals(weights: pd.DataFrame) -> None:
    for _, row in weights.iterrows():
        ticker, weight = row.name, row["weight"]
        if weight > 0.02:
            send_telegram_alert(f"🔔 *Signal d'achat* : {ticker} ({weight:.1%})")

def monitor_portfolio_performance(backtest_result: dict) -> None:
    stats = backtest_result.get("stats", {})
    sharpe = stats.get("Sharpe Ratio", 0)
    max_dd = stats.get("Max Drawdown", 0)
    
    if sharpe < 0.5:
        send_telegram_alert(f"⚠️ Sharpe faible : {sharpe:.2f}")
    if max_dd < -0.20:
        send_telegram_alert(f"⚠️ Drawdown important : {max_dd:.1%}")

def weekly_report() -> None:
    send_telegram_alert(f"📊 *Rapport hebdomadaire* - {datetime.now().strftime('%Y-%m-%d')}")

def start_scheduler() -> None:
    schedule.every().monday.at("08:00").do(weekly_report)
    schedule.every().day.at("09:00").do(lambda: print("Checking signals..."))
    
    while True:
        schedule.run_pending()
        time.sleep(3600)