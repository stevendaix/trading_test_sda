import yfinance as yf
import duckdb
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import time

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "market_data.db"
CACHE_DIR = DATA_DIR / "cache"
FRED_API_KEY = os.getenv("FRED_API_KEY", "abcdefghijklmnopqrstuvwxyz123456")

CACHE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

def init_database():
    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            ticker VARCHAR,
            date DATE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume BIGINT,
            adj_close DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            ticker VARCHAR,
            date DATE,
            pe_ratio DOUBLE,
            pb_ratio DOUBLE,
            dividend_yield DOUBLE,
            market_cap DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS universe (
            ticker VARCHAR,
            yahoo_ticker VARCHAR,
            name VARCHAR,
            sector VARCHAR,
            exchange VARCHAR,
            eligible_pea BOOLEAN,
            type VARCHAR
        )
    """)
    con.close()

def load_pea_universe(csv_path: Path = Path(__file__).parent.parent / "config" / "pea_universe.csv"):
    if csv_path and csv_path.exists():
        df = pd.read_csv(csv_path)
        if "yahoo_ticker" in df.columns:
            return df
    return pd.DataFrame({
        "ticker": ["MC.PA"],
        "yahoo_ticker": ["MC.PA"],
        "name": ["LVMH"],
        "sector": ["Consumer"],
        "exchange": ["EPA"],
        "eligible_pea": [True],
        "type": ["stock"]
    })

def download_price_data(universe_df: pd.DataFrame, start_date: str = "2014-01-01", end_date: str = None):
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    all_data = []
    for _, row in universe_df.iterrows():
        yahoo_ticker = row.get("yahoo_ticker", row["ticker"])
        ticker = row["ticker"]
        try:
            data = yf.download(yahoo_ticker, start=start_date, end=end_date)
            if not data.empty:
                data = data.reset_index()
                if isinstance(data.columns[0], tuple):
                    data.columns = [c[0] if c[1] == "" else c[0].lower() for c in data.columns]
                data["ticker"] = ticker
                data = data.rename(columns={"Close": "close", "High": "high", "Low": "low", "Open": "open", "Volume": "volume"})
                if "adj_close" not in data.columns:
                    data["adj_close"] = data["close"]
                all_data.append(data[["ticker", "Date", "open", "high", "low", "close", "volume", "adj_close"]])
                time.sleep(0.1)
            else:
                print(f"No data for {yahoo_ticker}")
        except Exception as e:
            print(f"Error downloading {yahoo_ticker}: {e}")
    
    if all_data:
        df = pd.concat(all_data, ignore_index=True)
        df = df.rename(columns={"Date": "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df[["ticker", "date", "open", "high", "low", "close", "volume", "adj_close"]]
    return pd.DataFrame()

def calculate_fundamentals(universe_df: pd.DataFrame):
    fundamentals = []
    for _, row in universe_df.iterrows():
        if row.get("type", "stock") == "etf":
            continue
        yahoo_ticker = row.get("yahoo_ticker", row["ticker"])
        ticker = row["ticker"]
        try:
            stock = yf.Ticker(yahoo_ticker)
            info = stock.info
            fundamentals.append({
                "ticker": ticker,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap")
            })
            time.sleep(0.1)
        except Exception as e:
            print(f"Error getting fundamentals for {yahoo_ticker}: {e}")
    
    return pd.DataFrame(fundamentals)

def update_database(universe_df: pd.DataFrame, prices_df: pd.DataFrame, fundamentals_df: pd.DataFrame):
    con = duckdb.connect(str(DB_PATH))
    
    con.execute("DELETE FROM universe")
    for _, row in universe_df.iterrows():
        con.execute("""
            INSERT INTO universe (ticker, yahoo_ticker, name, sector, exchange, eligible_pea, type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tuple(row))
    
    if not prices_df.empty:
        existing = con.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
        if existing == 0:
            for _, row in prices_df.iterrows():
                con.execute("""
                    INSERT INTO prices (ticker, date, open, high, low, close, volume, adj_close)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, tuple(row))
        else:
            for _, row in prices_df.iterrows():
                con.execute("""
                    INSERT OR REPLACE INTO prices (ticker, date, open, high, low, close, volume, adj_close)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, tuple(row))
    
    if not fundamentals_df.empty:
        for _, row in fundamentals_df.iterrows():
            con.execute("""
                INSERT OR REPLACE INTO fundamentals (ticker, date, pe_ratio, pb_ratio, dividend_yield, market_cap)
                VALUES (?, ?, ?, ?, ?, ?)
            """, tuple(row))
    
    con.close()

def main():
    init_database()
    
    universe_df = load_pea_universe()
    
    print(f"Downloading price data for {len(universe_df)} tickers...")
    prices_df = download_price_data(universe_df)
    
    print("Calculating fundamentals...")
    fundamentals_df = calculate_fundamentals(universe_df)
    
    print("Updating database...")
    update_database(universe_df, prices_df, fundamentals_df)
    
    print(f"Data pipeline complete. Database saved to {DB_PATH}")

if __name__ == "__main__":
    main()