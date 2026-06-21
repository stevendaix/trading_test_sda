# Setup & Execution

## Installation
```bash
cd /home/steven/podcast/trading_test_sda
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Execution
```bash
# Collecte données PEA
python src/data_collector.py

# Test rapide
pytest tests/test_data_collector.py -v
```

## Structure Phase 1-2-3 complète
- `data_collector.py` → DuckDB avec OHLCV + fondamentaux
- `indicators.py` → Value/Momentum scores
- `backtester.py` → VectorBT avec frais 0.5%
- `portfolio_optimizer.py` → Max 5% par action
- `strategy.py` → Orchestration
- `monitor.py` → Alertes Telegram (nécessite TELEGRAM_BOT_TOKEN)