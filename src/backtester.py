import vectorbt as vbt
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "market_data.db"

TradingFee = 0.005
TransactionCost = TradingFee

def run_backtest(prices: pd.DataFrame, signals: pd.DataFrame) -> dict:
    entries = signals["buy_signal"].fillna(False)
    exits = signals["sell_signal"].fillna(False)
    
    portfolio = vbt.Portfolio.from_signals(
        close=prices["close"],
        entries=entries,
        exits=exits,
        freq="1D",
        fees=TransactionCost,
        slippage=0.001,
        direction="both",
        cash_sharing=True,
        group_by=True
    )
    
    return {
        "portfolio": portfolio,
        "stats": portfolio.stats(),
        "total_return": portfolio.total_return(),
        "sharpe_ratio": portfolio.sharpe_ratio(),
        "max_drawdown": portfolio.max_drawdown(),
        "win_rate": portfolio.win_rate()
    }

def calculate_signals_from_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df["buy_signal"] = (
        (df.get("value_score", 0) > 0.6) &
        (df.get("above_sma_200", True)) &
        (df.get("rsi_14", 50) < 70)
    )
    
    df["sell_signal"] = (
        (df.get("rsi_14", 50) > 70) |
        (~df.get("above_sma_200", True))
    )
    
    return df

def optimize_parameters(prices: pd.DataFrame, indicator_func, param_grid: dict) -> dict:
    import optuna
    
    def objective(trial):
        value_threshold = trial.suggest_float("value_threshold", 0.4, 0.8)
        rsi_threshold = trial.suggest_int("rsi_threshold", 60, 80)
        
        signals = calculate_signals_from_indicators(prices)
        signals["buy_signal"] = signals["value_score"] > value_threshold
        
        if signals["buy_signal"].sum() == 0:
            return -0.5
        
        result = run_backtest(prices, signals)
        return result.get("sharpe_ratio", {}).get("Sharpe Ratio", 0)
    
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50)
    
    return {
        "best_params": study.best_params,
        "best_value": study.best_value
    }

def generate_signals_from_db(conn, date: str = None) -> pd.DataFrame:
    if date is None:
        query = """
            SELECT p.*, f.pe_ratio, f.pb_ratio, f.dividend_yield
            FROM prices p
            LEFT JOIN fundamentals f ON p.ticker = f.ticker
            WHERE p.date = (SELECT MAX(date) FROM prices)
        """
    else:
        query = f"""
            SELECT p.*, f.pe_ratio, f.pb_ratio, f.dividend_yield
            FROM prices p
            LEFT JOIN fundamentals f ON p.ticker = f.ticker
            WHERE p.date = '{date}'
        """
    
    return conn.execute(query).fetchdf()