import pytest
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collector import load_pea_universe, init_database, DB_PATH

class TestDataCollector:
    def test_load_pea_universe(self):
        df = load_pea_universe()
        assert df is not None
        assert len(df) > 0
        assert "ticker" in df.columns
        assert "yahoo_ticker" in df.columns
        assert "type" in df.columns
    
    def test_universe_has_etfs(self):
        df = load_pea_universe()
        etfs = df[df["type"] == "etf"]
        assert len(etfs) >= 9
    
    def test_universe_has_stocks(self):
        df = load_pea_universe()
        stocks = df[df["type"] == "stock"]
        assert len(stocks) >= 50
    
    def test_init_database(self, tmp_path):
        import duckdb
        test_db = tmp_path / "test_market.db"
        original_db = DB_PATH
        
        import src.data_collector as dc
        dc.DB_PATH = test_db
        
        dc.init_database()
        
        assert test_db.exists()
        con = duckdb.connect(str(test_db))
        tables = con.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]
        assert "prices" in table_names
        assert "fundamentals" in table_names
        assert "universe" in table_names
        con.close()