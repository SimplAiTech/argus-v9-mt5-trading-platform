# ARGUS V9 — Risk Management

## Overview

Risk management in ARGUS V9 operates at multiple levels simultaneously. A signal can be blocked at any of these levels before it reaches execution. The goal is to protect your account from drawdown while allowing the strategies' statistical edge to play out over time.

---

## Level 1: Account Contract (Prop Firm Rules)

**File:** `argus_vision/core/contract.py`

The Account Contract is the first and hardest gate. It enforces your prop firm's specific rules as configured in the **Accounts** tab.

### Parameters

| Parameter | Where to set | What it protects |
|-----------|-------------|------------------|
| `prop_initial_balance` | Accounts tab | Starting balance reference for drawdown calculation |
| `max_drawdown_usd` | Accounts tab | Maximum total loss from starting balance (hard stop) |
| `daily_loss_limit_usd` | Accounts tab | Maximum loss in a single calendar day |
| `max_trades_per_day` | Accounts tab | Maximum number of trades per day |

### How Drawdown Is Calculated

```
allowed_floor = prop_initial_balance - max_drawdown_usd
current_equity = MT5 equity (includes open positions)

if current_equity ≤ allowed_floor:
    → HARD_STOP_DRAWDOWN
    → No new trades until next session / manual reset
```

> **Example:** $50,000 account with $2,500 max drawdown → floor is $47,500. If equity drops to $47,499, trading halts.

### Daily Loss

```
today_loss = realized PnL today + unrealized PnL of open positions (if negative)

if abs(today_loss) ≥ daily_loss_limit_usd:
    → DAILY_LIMIT_REACHED
    → No new trades until midnight UTC
```

### Important Notes

- `max_drawdown_usd = 0` means **no drawdown limit** (unlimited). Do not confuse this with a $0 limit.
- The contract values are cached in memory (`_contract_cache`) after initial load. Changes in the Accounts tab take effect on the next ARGUS restart.
- At startup, MT5 equity may not be synced yet (shows 0 or 1). ARGUS detects this (`equity ≤ 1.0`) and returns `OK_CONTEXT_LOADING` instead of triggering a false HARD_STOP.

---

## Level 2: Risk Engine — Position Sizing

**File:** `argus_vision/core/risk.py`

Calculates the correct lot size for every trade so that your risk per trade is always a fixed percentage of equity, regardless of the instrument or SL distance.

### Calculation

```
risk_amount ($) = equity × risk_per_trade_pct / 100

pip_value ($)   = contract_size × pip_size × (1 / quote_price)
                  (adjusted for account currency)

lot_size        = risk_amount / (sl_pips × pip_value)
lot_size        = round down to broker's volume_step
lot_size        = clamp to [volume_min, volume_max]
```

### Example

- Account equity: $10,000
- Risk per trade: 1% → risk $100
- EURUSD, SL = 20 pips
- Pip value for 1 lot EURUSD ≈ $10
- Lot size = $100 / (20 × $10) = **0.50 lots**

### Minimum SL Override (BTC/ETH)

For instruments priced above $1,000, the strategy's default `sl_pips` can be too small in absolute dollar terms, causing broker rejection (error 10016 — invalid stops).

ARGUS enforces a minimum SL of **0.3% of the current price** for these instruments:

```python
if price > 1000 and sl_distance < price * 0.003:
    sl_distance = price * 0.003
```

This ensures SL is always broker-valid for high-priced assets.

---

## Level 3: AI Signal Filter

**Model:** `argus_ai_model_v3.joblib`  
**AUC:** 0.77  
**Threshold:** 0.40

Every signal receives a confidence score from the ML model. Only signals with a score ≥ 0.40 are allowed through. This filter eliminates approximately 30–40% of raw signals, improving the quality of what reaches execution.

The threshold is configurable per strategy via `ai_min_confidence` in `config.json`. Lowering it lets more signals through; raising it is more selective but reduces trade frequency.

---

## Level 4: News Guard

**File:** `argus_vision/core/news/guard.py`

High-impact economic events cause extreme short-term volatility that invalidates normal price behavior. The news guard blocks all new signals for affected currency pairs within a window around each event.

### Protected events (examples)

| Event | Pairs affected |
|-------|---------------|
| Non-Farm Payrolls | USD pairs, NAS100, XAUUSD |
| FOMC Rate Decision | USD pairs, NAS100, XAUUSD |
| CPI/PPI Releases | USD pairs |
| ECB Rate Decision | EUR pairs |
| BOE Rate Decision | GBP pairs |
| BOJ Policy | JPY pairs |

### Block window

Default: **30 minutes before and after** the scheduled event time.

---

## Level 5: Consistency Monitor

**File:** `argus_vision/core/consistency.py`

Detects abnormal trading behavior patterns and temporarily pauses new signal generation:

- **Loss streak detection:** If N consecutive trades close at a loss, new signals are paused for a cooldown period
- **Frequency spike:** If trade frequency exceeds normal bounds in a short window, new entries are paused
- **Auto-resume:** The pause lifts automatically after the cooldown period

This prevents the system from over-trading in unfavorable market conditions.

---

## Position-Level Risk: ScaleOut

After a position is open and in profit, ScaleOut manages the exit:

| Event | Action |
|-------|--------|
| Profit reaches 1R | Close 50% of position, move SL to breakeven |
| SL hit (remaining 50%) | Worst case: breakeven on the trade |
| TP hit (remaining 50%) | Full 1R profit on the remaining half |

**Net result:** A trade that hits 1R and then gets stopped at breakeven closes with +0.5R (profit). A trade that hits full TP closes with +1.5R total.

TrailingStop and BreakEvenManager are currently **disabled** — the system uses fixed SL/TP levels that match the backtest configuration exactly.

---

## Risk Parameter Recommendations by Account Size

| Account Size | Risk per Trade | Max Daily Loss | Max Drawdown |
|-------------|---------------|----------------|--------------|
| $5,000 – $10,000 | 1.0% | 3–4% | 6–8% |
| $10,000 – $25,000 | 0.75–1.0% | 3% | 5–6% |
| $25,000 – $100,000 | 0.5–0.75% | 2–3% | 4–5% |
| $100,000+ | 0.25–0.5% | 2% | 3–4% |

> These are general guidelines. Always set parameters to match your specific prop firm's rules exactly. Violating prop firm rules voids the challenge.

---

## Common Prop Firm Rules Reference

| Firm | Max Total DD | Daily Loss | Notes |
|------|-------------|-----------|-------|
| FTMO | 10% | 5% | Trailing drawdown from peak equity |
| FundedNext | 10% | 5% | From initial balance |
| MyForexFunds | 12% | 5% | — |
| E8 Funding | 8% | 4% | — |

> Always verify current rules on your firm's official website. Rules change.

---

## Error Codes Reference

| MT5 Error | Meaning | ARGUS Response |
|-----------|---------|----------------|
| 10016 | Invalid SL/TP (too tight) | Retry with minimum SL override |
| 10019 | Not enough money | Log error, skip trade |
| 10026 | Autotrading disabled in MT5 | Log critical error |
| 10004 | Requote | Retry with market execution |
