# 08 — NinjaTrader 8 node and ML training

## NinjaTrader 8 execution node (futures / prop accounts)

`ninja_node.py` is a standalone execution node for NinjaTrader 8 (e.g. FundedNext Futures).
It polls the same Supabase `trade_queue` as the MT5 terminals, takes signals assigned to NinjaTrader
accounts, and executes them through a file-based bridge. It runs alongside `ARGUS_TERMINAL.py`; the two don't interfere.

Order flow:
Python (`ninja_ati/ati_bridge.py`) writes JSON orders to `Documents\NinjaTrader 8\argus_orders\`,
the NinjaScript strategy `ARGUSListener` executes them with NT8's native order management, and it writes fill status
to `Documents\NinjaTrader 8\argus_status\`, which Python reads back. `ninja_ati/risk_manager.py` holds the daily-loss and
drawdown guards for the NT accounts.

Install `ARGUSListener`:
1. NinjaTrader 8 → Tools → Edit NinjaScript → Strategy → create a new strategy named `ARGUSListener`.
2. Paste `ninja_ati/ARGUSListener.cs` over the default content and compile (F5).
3. Apply the strategy to any chart (any instrument and timeframe). It runs as a background service.
4. Start `python ninja_node.py`.

## ML signal filter: retraining

- `collect_dataset.py` builds the training dataset from the history of signals and their outcomes.
- `train_model.py` trains the RandomForest classifier and prints the classification report and confusion matrix.
- The trained model ships as `argus_ai_model_v3.joblib`; the confidence threshold lives in `config.json` → `ai_settings`.
