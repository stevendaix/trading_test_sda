import pandas as pd
from pathlib import Path
from datetime import datetime

from data_collector import load_pea_universe, init_database, download_price_data, calculate_fundamentals, update_database
from indicators import calculate_all_indicators, get_top_candidates
from backtester import run_backtest, calculate_signals_from_indicators
from portfolio_optimizer import optimize_portfolio, apply_position_constraints

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "market_data.db"

def generate_portfolio_signals(n_candidates: int = 30) -> dict:
    universe_df = load_pea_universe()
    tickers = universe_df["ticker"].tolist()
    
    prices_df = download_price_data(tickers)
    fundamentals_df = calculate_fundamentals(tickers)
    
    indicators_df = calculate_all_indicators(prices_df, fundamentals_df)
    
    top_stocks = get_top_candidates(indicators_df, n=n_candidates)
    
    signals_df = calculate_signals_from_indicators(top_stocks)
    
    backtest_result = run_backtest(top_stocks, signals_df)
    
    weights = optimize_portfolio(prices_df, signals_df)
    constrained_weights = apply_position_constraints(weights)
    
    return {
        "tickers": tickers,
        "indicators": indicators_df,
        "signals": signals_df,
        "backtest": backtest_result,
        "weights": constrained_weights
    }

def run_monthly_rebalance() -> pd.DataFrame:
    result = generate_portfolio_signals()
    return result["weights"]

def export_signals_for_trading(weights: pd.DataFrame, output_file: str = "signals.csv") -> None:
    output_path = DATA_DIR / output_file
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    signals = weights[weights["weight"] > 0.001].copy()
    signals["date"] = timestamp
    signals["action"] = "BUY"
    
    signals.to_csv(output_path, index=False)
    print(f"Signals exported to {output_path}")