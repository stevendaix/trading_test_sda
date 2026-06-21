# trading_test_sda

Trading strategy backtesting and analysis framework for PEA (French equity accounts).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Quick Start

```bash
# Download market data (creates data/market_data.db - ~13MB, 87 tickers)
python src/data_collector.py

# Run backtest
python -c "from src.strategy import generate_portfolio_signals; r = generate_portfolio_signals(); print(r['backtest'])"

# Run tests
pytest tests/
```

## Project Structure

- `src/` - Source code
  - `data_collector.py` - OHLCV collection → DuckDB
  - `indicators.py` - SMA200, RSI14, volume, value scores
  - `backtester.py` - VectorBT backtesting with 0.5% PEA fees
  - `portfolio_optimizer.py` - PyPortfolioOpt with 5% max position
  - `strategy.py` - Orchestration
  - `monitor.py` - Telegram alerts
- `config/` - PEA universe (85 stocks + 8 ETF)
- `tests/` - Unit tests (5 tests)
- `data/` - Market data (market_data.db - gitignored)

## Features

- **PEA-compliant universe**: European stocks and ETFs only
- **Smart Money Scanner**: Trend + volume + value composite score
- **Backtesting**: 12 years history, 0.5% transaction costs
- **Optimization**: Max Sharpe with L2 regularization