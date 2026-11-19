# ARGUS V9 — Signal Pipeline

## Overview

Every trade signal in ARGUS passes through a strict multi-stage validation pipeline before it reaches your MT5 account. This document describes each stage, what it checks, and what happens when a signal is rejected.

---

## Pipeline Stages

```
MT5 OHLCV Data
      │
      ▼
 ┌────────────┐
 │  Strategy  │  Detects setup: FVG / Breakout / OrderBlock / Scalp
 └─────┬──────┘
       │ raw signal candidate
       ▼
 ┌─────────────────┐
 │ Account Contract│  Checks prop firm rules (drawdown, daily loss, trade count)
 └─────┬───────────┘
       │ PASS / HARD_STOP / DAILY_LIMIT
       ▼
 ┌─────────────┐
 │ Risk Engine │  Calculates lot size based on risk%, equity, SL distance
 └─────┬───────┘
       │ PASS / SIZE_ZERO / HARD_STOP
       ▼
 ┌──────────────┐
 │ AI Validator │  ML model scores signal confidence (threshold: 0.40)
 └─────┬────────┘
       │ PASS / REJECTED (low confidence)
       ▼
 ┌────────────┐
 │ News Guard │  Checks for high-impact events within ±30 min
 └─────┬──────┘
       │ PASS / BLOCKED
       ▼
 ┌──────────────────────┐
 │ Consistency Monitor  │  Anti-gamble filter — limits loss streaks
 └─────┬────────────────┘
       │ PASS / PAUSED
       ▼
 trade_queue INSERT (status: PENDING)
       │
       ▼
 MultiAccountEngine executes on MT5
       │
       ▼
 status → EXECUTED  (or FAILED)
```

---

## Stage 1: Strategy Detection

BrainEngine runs a 30-second cycle. Each cycle fetches OHLCV candles from MT5 for every active symbol/timeframe combination and runs the configured strategies.

**Data fetched per symbol:**
- Multiple timeframes simultaneously (e.g., M5 + M15 + H1 + H4)
- Last 500 candles per timeframe
- Uses `mt5.copy_rates_from_pos()`

**Account switch guard:** If the MT5 terminal is currently on a secondary account (MultiAccountEngine switched to it), `fetch_candles()` detects this and returns `None` silently. The brain cycle is skipped for that symbol. No error is logged.

---

## Stage 2: Account Contract Validation

**File:** `argus_vision/core/contract.py`

Enforces prop firm challenge rules per account:

| Check | Rule |
|-------|------|
| Total drawdown | Current equity vs. `prop_initial_balance - max_drawdown_usd` |
| Daily loss | Today's realized + unrealized loss vs. `daily_loss_limit_usd` |
| Max trades | Total filled trades today vs. `max_trades_per_day` |

**Outcomes:**
- `PASS` — signal continues
- `HARD_STOP_DRAWDOWN` — total drawdown limit hit, trading halted for this account
- `DAILY_LIMIT_REACHED` — daily loss cap hit, no new trades today
- `OK_CONTEXT_LOADING` — equity not yet synced from MT5 (startup), signal skipped safely

> **Important:** `max_drawdown_usd = 0` means no limit. Never set this to a fallback of 1000 — that would incorrectly halt a $6,000+ account.

---

## Stage 3: Risk Engine

**File:** `argus_vision/core/risk.py`

Calculates position size in lots:

```
risk_amount = equity × risk_per_trade_pct
pip_value   = contract_size × pip_size
lot_size    = risk_amount / (sl_pips × pip_value)
lot_size    = round to broker's volume_step
```

**Guards:**
- If `equity ≤ 1.0` → returns `OK_CONTEXT_LOADING` (MT5 not yet synced, prevents false HARD_STOP)
- If `lot_size < volume_min` → signal is rejected (too small to execute)

**Minimum SL override:** For assets priced above $1,000 (BTC, ETH), a minimum SL of 0.3% of current price is enforced, preventing broker rejection due to unrealistically tight stops.

---

## Stage 4: AI Validator

**File:** `argus_vision/core/ai/validator.py`  
**Model:** `argus_ai_model_v3.joblib`  
**AUC:** 0.77  
**Threshold:** 0.40 (production)

The ML model scores each signal using ~40 technical features including:
- RSI, ATR, EMA crossovers
- Volume ratios
- Market regime (trending vs. ranging)
- Session context (London, NY, Asia)
- Time of day

Signals with confidence < 0.40 are discarded. The model's confidence distribution clusters around 0.25–0.45, so the threshold is deliberately low to allow the best setups through while filtering noise.

---

## Stage 5: News Guard

**File:** `argus_vision/core/news/guard.py`

Fetches the economic calendar and blocks trades when a **high-impact** event is scheduled within a configurable window (default ±30 minutes) for the signal's currency pair.

High-impact events include: Non-Farm Payrolls, FOMC decisions, CPI releases, GDP announcements, central bank rate decisions.

If the news calendar is unavailable (network error), the guard defaults to **allow** (fail open), so a network blip never freezes trading.

---

## Stage 6: Consistency Monitor

**File:** `argus_vision/core/consistency.py`

An anti-gamble / consistency filter that detects:
- Unusual loss streaks (revenge trading pattern)
- Excessive position frequency in a short time window

When triggered, it pauses new signal generation temporarily and logs the event. This is a safeguard against the system over-trading during a bad market regime.

---

## trade_queue Record

When a signal passes all stages, it is inserted into Supabase `trade_queue`:

| Column | Value |
|--------|-------|
| `account_id` | UUID of the target account |
| `asset` | Symbol name (e.g., `XAUUSD`) |
| `direction` | `BUY` or `SELL` |
| `volume` | Calculated lot size |
| `sl` | Stop Loss price |
| `tp` | Take Profit price |
| `strategy_id` | e.g., `FVG`, `BREAKOUT` |
| `timeframe` | e.g., `H1`, `M15` |
| `status` | `PENDING` → `PROCESSING` → `EXECUTED` / `FAILED` |

> **Column note:** The column is `asset`, not `symbol`. And `volume`, not `quantity`. This is the source of truth.

---

## Execution by MultiAccountEngine

MultiAccountEngine polls `trade_queue` every 2 seconds for `PENDING` signals. For each signal:

1. Sets status to `PROCESSING` (prevents double execution)
2. Switches MT5 to the target account via `mt5.login()`
3. Resolves the broker-specific symbol name
4. Sends `order_send()` to MT5
5. Updates status to `EXECUTED` (success) or `FAILED` (error)
6. Restores MT5 to the primary account
7. Sends Telegram notification to the account owner

---

## ScaleOut (Partial Close)

After a position is open, ScaleOut monitors it every 30 seconds (per account). When unrealized profit reaches **1R** (equal to the initial risk amount):

- Closes **50%** of the position
- Moves Stop Loss to breakeven

This locks in profit while keeping half the position running for further gains.
