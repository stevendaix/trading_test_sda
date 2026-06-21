# Questions sur le projet trading_test_sda

## 1. Priorité de développement
**✅ Phase 1 : Fondation (collecte de données + DuckDB)** - Compléter
**✅ Phase 2 : Indicateurs (value/quality/momentum)** - Compléter
**🔄 Phase 3 : Stratégie & Backtesting** - En cours

## 2. Source de données fondamentales
**✅ Hybrid : `yfinance` + fichier CSV curaté + `openbb-sdk`**
- ✅ `data_collector.py` généré avec yfinance et cache

## 3. Univers boursier
**✅ VALIDÉ** - ~150 valeurs PEA-éligibles (stocks + ETFs)

## 4. Broker pour exécution
**✅ Exécution manuelle assistée par signaux**

## 5. Fonctionnalités générées
1. ✅ `data_collector.py` - Collecte OHLCV + fondamentaux → DuckDB
2. ✅ `indicators.py` - Calcul indicateurs value/momentum
3. ✅ `backtester.py` - VectorBT avec frais PEA (0.5%)
4. `portfolio_optimizer.py` - À générer
5. `strategy.py` - À générer

---

## Prochaines étapes

- Générer `portfolio_optimizer.py` avec PyPortfolioOpt
- Générer `strategy.py` avec orchestration
- Tests d'intégration avec vraies données