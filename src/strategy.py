import pandas as pd
from pathlib import Path
from datetime import datetime
import duckdb

from data_collector import load_pea_universe, init_database, DB_PATH
from indicators import smart_money_scanner, calculate_value_indicators
from backtester import run_backtest, calculate_signals_from_indicators
from portfolio_optimizer import optimize_portfolio, apply_position_constraints

DATA_DIR = Path(__file__).parent.parent / "data"

def generate_portfolio_signals(n_candidates: int = 30) -> dict:
    universe_df = load_pea_universe()
    
    con = duckdb.connect(str(DB_PATH))
    prices_df = con.execute("SELECT * FROM prices ORDER BY ticker, date").fetchdf()
    fundamentals_df = con.execute("SELECT * FROM fundamentals").fetchdf()
    
    indicators_df = smart_money_scanner(prices_df)
    indicators_df = calculate_value_indicators(indicators_df, fundamentals_df)
    
    signals_df = calculate_signals_from_indicators(indicators_df)
    
    # Run backtest on all tickers
    backtest_result = run_backtest(prices_df, signals_df)
    
    # Get top candidates for portfolio
    latest_signals = signals_df[signals_df["date"] == signals_df["date"].max()].copy()
    top_stocks = latest_signals[latest_signals["buy_signal"]].nlargest(n_candidates, "smart_money_score")
    
    weights = optimize_portfolio(prices_df, top_stocks)
    constrained_weights = apply_position_constraints(weights)
    
    return {
        "tickers": universe_df["ticker"].tolist(),
        "indicators": indicators_df,
        "signals": signals_df,
        "backtest": backtest_result,
        "weights": constrained_weights,
        "top_stocks": top_stocks
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