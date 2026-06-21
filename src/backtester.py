import vectorbt as vbt
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "market_data.db"

TradingFee = 0.005
TransactionCost = TradingFee

def run_backtest(prices: pd.DataFrame, signals: pd.DataFrame) -> dict:
    # Handle both long and wide formats
    if isinstance(prices, pd.DataFrame) and "ticker" in prices.columns:
        # Long format: pivot to wide
        close = prices.pivot(index="date", columns="ticker", values="close")
    else:
        # Already wide format
        close = prices
    
    # Extract signals
    if isinstance(signals, pd.DataFrame) and "ticker" in signals.columns and "buy_signal" in signals.columns:
        buy_signal = signals.pivot(index="date", columns="ticker", values="buy_signal")
        sell_signal = signals.pivot(index="date", columns="ticker", values="sell_signal")
    else:
        buy_signal = signals.get("buy_signal") if hasattr(signals, 'get') else signals
        sell_signal = signals.get("sell_signal") if hasattr(signals, 'get') else None
    
    # Align indices and columns
    if hasattr(buy_signal, 'columns'):
        common_cols = close.columns.intersection(buy_signal.columns)
        close = close[common_cols].dropna(how='all', axis=1)
        buy_signal = buy_signal[common_cols].fillna(False).astype(bool)
        sell_signal = sell_signal[common_cols].fillna(False).astype(bool)
    
    portfolio = vbt.Portfolio.from_signals(
        close=close,
        entries=buy_signal.astype(bool),
        exits=sell_signal.astype(bool),
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
        "win_rate": portfolio.stats()["Win Rate[%]"].mean() if "Win Rate[%]" in portfolio.stats() else None
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