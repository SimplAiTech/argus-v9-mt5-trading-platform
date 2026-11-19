# ARGUS V9 — System Overview

## What Is ARGUS?

ARGUS V9 is an institutional-grade algorithmic trading automation system designed for prop firm traders and professional money managers. It connects to MetaTrader 5, analyzes the market using multiple quantitative strategies, validates signals through an AI filter, and executes trades across one or more accounts — all automatically.

---

## Core Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Cloud-decoupled** | Brain publishes signals to Supabase; execution reads from it. Brain and executor can run on different machines. |
| **Multi-account** | One brain feeds multiple MT5 accounts simultaneously, each with independent risk rules. |
| **Prop-firm aware** | Every signal passes through an Account Contract validator that enforces drawdown limits, daily loss caps, and trade frequency rules. |
| **AI-filtered** | An ML model (AUC=0.77) scores each signal before it enters the queue. Low-confidence setups are rejected. |
| **News-aware** | A news guard blocks trades around high-impact economic events automatically. |

---

## System Components

```
┌─────────────────────────────────────────────────────────┐
│                    ARGUS TERMINAL (GUI)                  │
│                                                         │
│   Login → Connect MT5 → Enable AutoFlow                 │
│                                                         │
│   ┌──────────────┐      ┌──────────────────────────┐   │
│   │  BrainEngine │      │  MultiAccountEngine       │   │
│   │  (thread)    │      │  (thread)                 │   │
│   │              │      │                           │   │
│   │  Analyzes    │      │  Polls trade_queue        │   │
│   │  market every│      │  every 2 seconds          │   │
│   │  30 seconds  │      │                           │   │
│   └──────┬───────┘      └────────────┬──────────────┘   │
│          │                           │                   │
└──────────┼───────────────────────────┼───────────────────┘
           │                           │
           ▼                           ▼
    ┌─────────────────────────────────────┐
    │           Supabase (Cloud DB)        │
    │                                     │
    │  trade_queue: PENDING → EXECUTED    │
    │  trading_accounts                   │
    │  positions_realtime                 │
    │  trades_log                         │
    └─────────────────────────────────────┘
```

---

## Startup Sequence

1. Ensure **MetaTrader 5 is running** with Algo Trading enabled
2. Run `python ARGUS_TERMINAL.py`
3. Log in with your Supabase email/password
4. Select your MT5 account and click **Connect**
5. Enable the **AutoFlow** toggle → BrainEngine and MultiAccountEngine start

> **Note:** `brain.py` is NOT run as a standalone process in production. It runs as a background thread inside ARGUS_TERMINAL.py.

---

## Signal Flow (Simplified)

```
MT5 market data
      │
      ▼
BrainEngine detects setup (FVG, Breakout, OrderBlock, Scalp)
      │
      ▼
Validation pipeline:
  1. Account Contract   — prop firm rules
  2. Risk Engine        — position sizing
  3. AI Validator       — ML confidence ≥ 0.40
  4. News Guard         — no high-impact events
  5. Consistency Monitor— anti-gamble filter
      │
      ▼
Signal published to trade_queue (status: PENDING)
      │
      ▼
MultiAccountEngine picks up signal
      │
      ▼
Executes on MT5 → updates status to EXECUTED
      │
      ▼
Telegram notification sent to account owner
```

---

## Key Files

| File | Role |
|------|------|
| `ARGUS_TERMINAL.py` | GUI, startup, all tab views |
| `brain.py` | Market analysis, signal generation |
| `ArgusMultiAccount.py` | Multi-account execution engine |
| `config.json` | Strategy parameters |
| `.env` | Secrets (Supabase, MT5, Telegram) |
| `argus_ai_model_v3.joblib` | ML model for signal filtering |

---

## Supported Instruments

| Category | Instruments |
|----------|-------------|
| Crypto | BTCUSD, ETHUSD |
| Indices | NAS100 / USTEC100 / NDX100 |
| Commodities | XAUUSD |
| Forex | EURUSD, GBPUSD, USDJPY |

---

## Active Strategies

| Strategy | Description |
|----------|-------------|
| **FVG** | Fair Value Gap — imbalance fill setups |
| **BREAKOUT** | Consolidation breakout with volume confirmation |
| **ORDERBLOCK** | Institutional order block re-test entries |
| **SCALP** | High-frequency short-duration setups on H1 |

---

## Platform Requirements

- **OS:** Windows only (MetaTrader 5 Python API is Windows-exclusive)
- **Python:** 3.10 or higher
- **MetaTrader 5:** Must be running with Algo Trading enabled
- **Internet:** Required for Supabase sync and news guard
