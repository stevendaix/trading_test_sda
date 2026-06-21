import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent

def calculate_moving_averages(prices_df: pd.DataFrame) -> pd.DataFrame:
    df = prices_df.copy()
    df = df.sort_values(["ticker", "date"])
    
    df["sma_50"] = df.groupby("ticker")["close"].transform(
        lambda x: x.rolling(50).mean()
    )
    df["sma_200"] = df.groupby("ticker")["close"].transform(
        lambda x: x.rolling(200).mean()
    )
    
    df["above_sma_50"] = df["close"] > df["sma_50"]
    df["above_sma_200"] = df["close"] > df["sma_200"]
    df["trend_green"] = df["above_sma_50"] & df["above_sma_200"]
    
    return df

def calculate_volume_indicators(prices_df: pd.DataFrame) -> pd.DataFrame:
    df = prices_df.copy()
    
    df["dollar_volume"] = df["close"] * df["volume"]
    df["avg_volume_30d"] = df.groupby("ticker")["dollar_volume"].transform(
        lambda x: x.rolling(30).mean()
    )
    
    df["volume_spike"] = df["dollar_volume"] > 2 * df["avg_volume_30d"]
    df["volume_ok"] = df["avg_volume_30d"] > 1000000
    
    return df

def calculate_relative_strength(prices_df: pd.DataFrame, benchmark_df: pd.DataFrame = None) -> pd.DataFrame:
    df = prices_df.copy()
    
    if benchmark_df is not None:
        merged = df.merge(benchmark_df, on="date", suffixes=("", "_bench"))
        merged["relative_return"] = merged["close"] / merged["close_bench"]
        return merged
    
    df["relative_return"] = 1.0
    return df

def calculate_rsi(prices_df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    import vectorbt as vbt
    df = prices_df.copy()
    df = df.sort_values(["ticker", "date"])
    
    close = df.pivot(index="date", columns="ticker", values="close")
    rsi = vbt.RSI.run(close, window=window).rsi
    if isinstance(rsi.columns[0], tuple):
        rsi.columns = [c[1] for c in rsi.columns]
    rsi_long = rsi.melt(ignore_index=False, var_name="ticker", value_name="rsi_14").reset_index()
    df = df.merge(rsi_long, on=["date", "ticker"])
    return df

def smart_money_scanner(prices_df: pd.DataFrame) -> pd.DataFrame:
    df = prices_df.copy()
    
    df = calculate_moving_averages(df)
    df = calculate_volume_indicators(df)
    df = calculate_rsi(df)
    
    df["trend_score"] = df["trend_green"].astype(int) + df["above_sma_200"].astype(int)
    df["volume_score"] = df["volume_spike"].astype(int) + df["volume_ok"].astype(int)
    
    df["smart_money_score"] = (
        df["trend_score"] * 0.4 +
        df["volume_score"] * 0.6
    )
    
    return df

def calculate_value_indicators(prices_df: pd.DataFrame, fundamentals_df: pd.DataFrame) -> pd.DataFrame:
    merged = prices_df.merge(fundamentals_df, on="ticker", how="left", suffixes=("", "_fund"))
    
    # Handle date column duplication
    if "date_fund" in merged.columns:
        merged = merged.drop(columns=["date_fund"])
    
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

def calculate_smart_money_score(df: pd.DataFrame) -> pd.DataFrame:
    df = smart_money_scanner(df)
    df = calculate_value_indicators(df, pd.DataFrame())
    
    df["composite_score"] = (
        df["smart_money_score"] * 0.4 +
        df["value_score"] * 0.6
    )
    
    return df

def get_smart_money_signals(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    df = calculate_smart_money_score(df)
    df["buy_signal"] = (
        df["trend_green"] &
        df["volume_spike"] &
        (df["composite_score"] > threshold)
    )
    return df