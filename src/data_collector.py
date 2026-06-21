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

def validate_tickers(symbols: list, yahoo_tickers: list) -> tuple:
    import yfinance as yf
    valid_symbols = []
    valid_yahoo = []
    
    for t, y in zip(symbols, yahoo_tickers):
        try:
            ticker = yf.Ticker(y)
            info = ticker.info
            if info and info.get("regularMarketPrice") is not None:
                valid_symbols.append(t)
                valid_yahoo.append(y)
            else:
                print(f"⚠️ {t}/{y}: Ticker invalide - ignoré")
        except Exception:
            print(f"⚠️ {t}/{y}: Erreur - ignoré")
    
    return valid_symbols, valid_yahoo

def download_price_data(universe_df: pd.DataFrame, start_date: str = "2014-01-01", end_date: str = None):
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    symbols, yahoo_tickers = validate_tickers(
        universe_df["ticker"].tolist(),
        universe_df.apply(lambda r: r.get("yahoo_ticker", r["ticker"]), axis=1).tolist()
    )
    valid_df = universe_df[universe_df["ticker"].isin(symbols)].copy()
    
    all_data = []
    for _, row in valid_df.iterrows():
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
        prices_df.to_parquet("/tmp/prices_temp.parquet")
        con.execute("CREATE OR REPLACE TABLE prices AS SELECT * FROM read_parquet('/tmp/prices_temp.parquet')")
    
    if not fundamentals_df.empty:
        fundamentals_df.to_parquet("/tmp/fundamentals_temp.parquet")
        con.execute("CREATE OR REPLACE TABLE fundamentals AS SELECT * FROM read_parquet('/tmp/fundamentals_temp.parquet')")
    
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