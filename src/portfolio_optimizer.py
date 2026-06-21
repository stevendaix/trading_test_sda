import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

DATA_DIR = Path(__file__).parent.parent / "data"

def optimize_portfolio(prices_df: pd.DataFrame, signals_df: pd.DataFrame, risk_free_rate: float = 0.02) -> pd.DataFrame:
    from pypfopt import EfficientFrontier, risk_models, expected_returns, objective_functions
    
    pivot_prices = prices_df.pivot(index="date", columns="ticker", values="close")
    pivot_prices = pivot_prices.dropna(axis=1, how="all")
    pivot_prices = pivot_prices.ffill().bfill()
    
    returns = expected_returns.mean_historical_return(pivot_prices)
    cov_matrix = risk_models.sample_covariance(pivot_prices)
    
    ef = EfficientFrontier(returns, cov_matrix)
    ef.add_objective(objective_functions.L2_reg, gamma=0.1)
    
    weights = ef.max_sharpe(risk_free_rate=risk_free_rate)
    
    cleaned_weights = ef.clean_weights()
    performance = ef.portfolio_performance(verbose=False)
    
    return pd.DataFrame.from_dict(cleaned_weights, orient="index", columns=["weight"])

def apply_position_constraints(weights: pd.DataFrame, max_per_stock: float = 0.05) -> pd.DataFrame:
    total_weight = weights["weight"].sum()
    capped = weights["weight"].clip(upper=max_per_stock)
    capped = capped / capped.sum() * total_weight
    return capped.to_frame(name="weight")

def apply_sector_constraints(weights: pd.DataFrame, sectors: pd.Series, max_per_sector: float = 0.20) -> pd.DataFrame:
    df = weights.copy()
    df["sector"] = sectors
    
    sector_totals = df.groupby("sector")["weight"].sum()
    
    for sector in sector_totals.index:
        if sector_totals[sector] > max_per_sector:
            df.loc[df["sector"] == sector, "weight"] *= max_per_sector / sector_totals[sector]
    
    return df[["weight"]]

def get_etf_allocation(balance: float, etf_weights: dict) -> dict:
    return {etf: weight * balance for etf, weight in etf_weights.items()}

def rebalance_portfolio(current_weights: pd.DataFrame, target_weights: pd.DataFrame, threshold: float = 0.02) -> pd.DataFrame:
    trades = target_weights.merge(current_weights, on="ticker", how="outer", suffixes=("_target", "_current"))
    trades = trades.fillna(0)
    trades["target_weight"] = trades["weight_target"] - trades["weight_current"]
    trades["action"] = trades["target_weight"].apply(
        lambda x: "BUY" if x > threshold else ("SELL" if x < -threshold else "HOLD")
    )
    return trades[trades["action"] != "HOLD"]