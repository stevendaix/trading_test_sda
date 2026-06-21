# trading_test_sda

Trading strategy backtesting and analysis framework.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Project Structure

- `src/` - Source code
  - `backtest.py` - Core backtesting functions
- `tests/` - Unit tests
- `data/` - Market data and results
- `docs/` - Documentation

## Usage

```python
from backtest import load_data, run_backtest

# Load your market data
data = load_data("data/your_data.csv")

# Run backtest with your strategy
results = run_backtest(my_strategy, data)
```

## Testing

```bash
pytest tests/
```
