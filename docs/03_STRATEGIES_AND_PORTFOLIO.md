# ARGUS V9 — Strategies & Active Portfolio

## Overview

ARGUS V9 runs four active strategies across multiple instruments and timeframes simultaneously. Each strategy is independently configurable — you can enable/disable it, change risk parameters, and adjust timeframes from the **Strategies** tab in the GUI.

---

## Active Portfolio (as of 2026-03-20)

| Strategy | Active Combinations | Instruments | Timeframes |
|----------|---------------------|-------------|------------|
| **FVG** | 18 | BTCUSD, ETHUSD, XAUUSD, NAS100, USDJPY, GBPUSD, EURUSD | M5, M15, H1, H4 |
| **BREAKOUT** | 12 | ETHUSD, BTCUSD, XAUUSD, NAS100, USDJPY, EURUSD | M5, M15, H1, H4 |
| **ORDERBLOCK** | 5 | ETHUSD, BTCUSD, NAS100 | M15, H1, H4 |
| **SCALP** | 6 | EURUSD, GBPUSD, USDJPY, NAS100, BTCUSD, ETHUSD | H1 |
| TREND | — | — | disabled |
| GAP | — | — | disabled |

**Total active combinations: 41**

---

## Strategy Descriptions

### FVG — Fair Value Gap

A Fair Value Gap is a price inefficiency created when a large, fast candle leaves an imbalance between supply and demand. Price tends to return to fill this gap before continuing in the original direction.

**Entry logic:**
1. Detect a 3-candle FVG pattern (gap between candle 1 high/low and candle 3 low/high)
2. Wait for price to return into the gap
3. Enter in the direction of the original impulse
4. Set SL below the gap for bullish / above for bearish

**Best on:** XAUUSD, NAS100, BTCUSD (high liquidity assets with clean imbalances)

**Configurable parameters:**
- `fvg_min_pips` — minimum gap size to qualify
- `fvg_rr_ratio` — risk-reward ratio for TP placement
- `fvg_sl_pips` — stop loss size in pips

---

### BREAKOUT — Consolidation Breakout

Identifies periods of price consolidation (tight range) and trades the breakout when price exits the range with momentum.

**Entry logic:**
1. Detect a consolidation zone over N candles (ATR-based range tightness)
2. Wait for a candle close outside the zone
3. Enter in the breakout direction
4. Set SL inside the consolidation zone

**Best on:** ETHUSD, BTCUSD (high momentum crypto breakouts), XAUUSD H4

**Configurable parameters:**
- `breakout_lookback` — candles to define the consolidation
- `breakout_atr_multiplier` — minimum ATR expansion required
- `breakout_sl_pips` — stop loss size

---

### ORDERBLOCK — Institutional Order Block

Order Blocks are areas where institutional players (banks, market makers) placed large orders. Price frequently returns to these zones before continuing in the institutional direction.

**Entry logic:**
1. Identify a strong bearish/bullish candle followed by a significant move
2. Mark the candle's body as the Order Block zone
3. Enter when price returns to and respects the zone
4. SL beyond the Order Block high/low

**Implementation note:** ARGUS uses `OrderBlockBacktestStrategy` from `argus_vision/backtesting/strategies/` as the live OB strategy. This is intentional — the same code is used in both backtesting and live trading for consistency.

**Best on:** ETHUSD H1/H4, NAS100 H4, BTCUSD H4

---

### SCALP — Short-Duration H1 Setups

High-frequency strategy based on mean-reversion and momentum signals on the H1 timeframe. Uses tight SL and targets quick moves of 1–2x ATR.

**Entry logic:**
- RSI divergence + EMA confluence
- Only trades during London and New York sessions
- Avoids low-liquidity Asian session (except USDJPY)

**Best on:** Forex pairs (EURUSD, GBPUSD, USDJPY) and liquid indices

**SCALP backtest results (2 years, H1):**

| Symbol | Profit Factor | Win Rate | Return |
|--------|---------------|----------|--------|
| EURUSD | 1.79 | 47% | +4.0% |
| GBPUSD | 1.81 | 48% | +4.5% |
| USDJPY | 1.85 | 48% | +6.1% |
| NAS100 | 1.44 | 42% | +2.5% |
| BTCUSD | 1.41 | 42% | +3.0% |
| ETHUSD | 1.52 | 43% | +4.5% |

> XAUUSD SCALP was removed (PF 0.93, net loss over 2 years).

---

## Strategy Configuration

Each strategy's parameters are stored in `config.json` and editable from the **Strategies** tab in the GUI.

### Key parameters (apply to all strategies):

| Parameter | Description |
|-----------|-------------|
| `is_enabled` | Enable/disable the strategy |
| `sl_pips` | Stop Loss size in pips |
| `rr_ratio` | Risk-Reward ratio (TP = entry ± sl_pips × rr_ratio) |
| `risk_pct` | Risk percentage per trade (overrides account default) |
| `max_trades_per_day` | Maximum trades per day for this strategy |
| `ai_min_confidence` | Minimum AI score to accept a signal (default: 0.40) |

### SL/TP note

Trade queue stores SL and TP as **prices**, not pips. The conversion from pips to prices happens in `brain.py` at signal generation time using the current bid/ask price. This means SL/TP levels survive broker reconnects and account switches without recalculation.

---

## Adding a Custom Strategy

1. Create a strategy class in `argus_vision/backtesting/strategies/`
2. Implement `generate_signals(df)` returning a list of signal dicts
3. Register it in `brain.py` in the strategy router
4. Add its config section to `config.json`

Custom strategies automatically inherit the full validation pipeline (AI filter, news guard, risk engine, account contract).

---

## Disabled Strategies

### TREND
Trend-following strategy using EMA crossovers. Disabled because:
- High drawdown during ranging/choppy markets
- Performance does not meet the minimum PF threshold across the current portfolio

### GAP
Weekend gap filler (trades Sunday open gaps). Disabled because:
- Gap fills are increasingly rare on crypto/indices
- Insufficient edge over 2-year backtest period
