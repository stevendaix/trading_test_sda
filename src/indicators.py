import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

def calculate_value_indicators(prices_df: pd.DataFrame, fundamentals_df: pd.DataFrame) -> pd.DataFrame:
    merged = prices_df.merge(fundamentals_df, on="ticker", how="left")
    
    merged["pe_ratio"] = merged["pe_ratio"].clip(upper=100)
    merged["pb_ratio"] = merged["pb_ratio"].clip(upper=20)
    merged["dividend_yield"] = merged["dividend_yield"].fillna(0)
    
    merged["value_pe"] = (merged["pe_ratio"] < 15).astype(int)
    merged["value_pb"] = (merged["pb_ratio"] < 1.5).astype(int)
    merged["value_dividend"] = (merged["dividend_yield"] > 0.02).astype(int)
    
    merged["value_score"] = (
        merged["value_pe"] * 0.34 +
        merged["value_pb"] * 0.33 +
        merged["value_dividend"] * 0.33
    )
    
    return merged

def calculate_quality_indicators(prices_df: pd.DataFrame) -> pd.DataFrame:
    result = prices_df.copy()
    
    result["price_to_sma200"] = result["close"] / result["sma_200"]
    result["quality_momentum"] = result["price_to_sma200"] > 1
    
    return result

def calculate_momentum_indicators(prices_df: pd.DataFrame) -> pd.DataFrame:
    result = prices_df.copy()
    
    result["rsi_14"] = 50
    result["momentum_6m"] = 0.0
    result["momentum_12m"] = 0.0
    result["above_sma_200"] = result["close"] > result.get("sma_200", result["close"])
    
    return result

def calculate_all_indicators(prices_df: pd.DataFrame, fundamentals_df: pd.DataFrame) -> pd.DataFrame:
    result = calculate_value_indicators(prices_df, fundamentals_df)
    result = calculate_momentum_indicators(result)
    return result

def get_top_candidates(df: pd.DataFrame, n: int = 30, score_col: str = "value_score") -> pd.DataFrame:
    return df.nlargest(n, score_col)