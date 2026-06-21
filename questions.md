# Questions sur le projet trading_test_sda

## 1. Priorité de développement
**✅ Phase 1 : Fondation (collecte de données + DuckDB)** - Compléter

## 2. Source de données fondamentales
**✅ Hybrid : `yfinance` + fichier CSV curaté + `openbb-sdk` (en upgrade)**
- ✅ `data_collector.py` généré avec yfinance et cache

## 3. Univers boursier
**✅ VALIDÉ** - Tickers ETF PEA fournis et intégrés

## 4. Broker pour exécution
**✅ Exécution manuelle assistée par signaux** - Compléter

## 5. Fonctionnalités prioritaires
**✅ Ordre de génération recommandé :**
1. ✅ `data_collector.py` - Généré
2. `indicators.py` - Calcul value/quality/momentum
3. `backtester.py` - Validation des signaux
4. `portfolio_optimizer.py` - Allocation optimale
5. `strategy.py` - Orchestration finale + alertes

---

## Notes supplémentaires

### Kaggle dataset Yahoo Finance
- `list_tickers.json` et le dataset Kaggle contiennent des tickers US (non PEA compatibles)
- Ignorés pour ce projet PEA France

### FRED API
- `FRED_API_KEY` configurée dans `.env` (ignorer Phase 1-3)