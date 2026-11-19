# ARGUS V9 — Multi-Account Architecture

## Overview

ARGUS V9 supports managing multiple MT5 accounts simultaneously from a single running instance. All accounts share the same signal intelligence (one BrainEngine analyzes the market) but each account is executed independently with its own risk parameters, lot sizing, and prop firm rules.

---

## How Multiple Accounts Work

```
BrainEngine (one instance)
│
│  Analyzes market once for all accounts
│  Publishes ONE signal per account per setup
│
├──► trade_queue: PENDING (account_id = Account A)
├──► trade_queue: PENDING (account_id = Account B)
└──► trade_queue: PENDING (account_id = Account C)

MultiAccountEngine (one instance)
│
│  Polls every 2 seconds
│
├──► Switch MT5 to Account A → execute → restore
├──► Switch MT5 to Account B → execute → restore
└──► Switch MT5 to Account C → execute → restore
```

The key insight: **one MT5 terminal, multiple accounts**. MetaTrader 5 on Windows supports only one active account at a time. ARGUS switches between accounts using `mt5.login()`, executes the work, then restores the primary account. This switching is fast (~0.5–1 second per account) and happens transparently in the background.

---

## Account Registration

Each account is registered in Supabase `trading_accounts` with:

| Field | Description |
|-------|-------------|
| `mt5_login` | MT5 account number |
| `mt5_password` | MT5 account password |
| `mt5_server` | Broker server name |
| `prop_initial_balance` | Starting balance of the challenge |
| `max_drawdown_usd` | Maximum allowed total drawdown ($) |
| `daily_loss_limit_usd` | Maximum allowed daily loss ($) |
| `risk_per_trade_pct` | Risk percentage per trade |
| `max_trades_per_day` | Trade frequency limit |

All these values are set through the **Accounts** tab in the GUI when adding a new account.

---

## Symbol Resolution Per Broker

Different brokers name the same instrument differently. ARGUS resolves this automatically at execution time:

| Standard Name | Ox Securities | FundedNext | Other brokers |
|--------------|--------------|-----------|--------------|
| EURUSD | EURUSD.PRO | EURUSD | EURUSD.raw, EURUSD.m, etc. |
| XAUUSD | XAUUSD.PRO | XAUUSD | GOLD, XAUUSD.raw |
| NAS100/USTEC100 | USTEC100 | NDX100 | US100, NASDAQ100 |
| BTCUSD | BTCUSD | BTCUSD | BTCUSD.pro |
| ETHUSD | ETHUSD | ETHUSD | ETHUSD.pro |

The resolution process in `ArgusMultiAccount._resolve_symbol()`:
1. **Direct match** — exact symbol name exists on this broker
2. **Alias map** — known cross-broker aliases (USTEC100 ↔ NDX100)
3. **Suffix probing** — tries `.PRO`, `.raw`, `.ecn`, `.m` suffixes
4. **Substring match** — finds any symbol containing the base name

This means ARGUS works out-of-the-box with any MT5 broker without manual symbol configuration.

---

## Position Management Across Accounts

ScaleOut runs for every account, not just the primary one. When MultiAccountEngine visits a secondary account to execute a trade, it also runs the ScaleOut check while already logged in — no extra switching required.

**ScaleOut per account:**
- Runs while MultiAccountEngine is already logged into each account (every 30 seconds per account)
- Independently tracks which tickets have already been partially closed (`_partial_closed` set)
- Uses the broker's own `volume_step` and `volume_min` for the partial close calculation

---

## Account Isolation & Security

Each user sees **only their own accounts** in the GUI and only their own signals in `trade_queue`. This is enforced at two levels:

1. **Application level**: BrainEngine receives `user_id` from the authenticated Supabase session and filters all queries by it
2. **Database level**: Supabase Row Level Security (RLS) policies on the server ensure a user cannot read or modify another user's data, even if they try to query directly

The `SUPABASE_SERVICE_KEY` (which bypasses RLS) is never distributed to end users. Only the anonymous key is included, which is subject to RLS.

---

## The MT5 Account Switch Problem

Since one MT5 terminal can only be on one account at a time, there is a potential conflict: while MultiAccountEngine is on a secondary account, BrainEngine might try to fetch market data.

**The problem:** Secondary account has different symbols (no `.PRO` suffix). Fetching `EURUSD.PRO` on FundedNext returns `None`.

**The solution (implemented):**
- BrainEngine stores the primary account's login at startup (`_primary_mt5_login`)
- Before every data fetch in `fetch_candles()`, it checks if MT5 is still on the primary account
- If not → silently returns `None` without logging an error
- The next brain cycle (30 seconds later) will be back on the primary account

This means at most one brain cycle is skipped during an account switch, with no user-visible errors.

---

## Adding a New Account

1. In the ARGUS GUI, go to **Accounts** tab
2. Click **+ Add Account**
3. Enter MT5 login, password, server
4. Configure risk parameters (match your prop firm rules exactly)
5. Click **Save**

ARGUS will automatically:
- Add the account to Supabase `trading_accounts`
- Include it in the next MultiAccountEngine sync cycle
- Start receiving signals on the next brain cycle

No restart required.

---

## Supported Brokers

ARGUS has been tested with:
- **Ox Securities** — uses `.PRO` suffix (EURUSD.PRO, XAUUSD.PRO, etc.)
- **FundedNext** — plain symbol names (EURUSD, NDX100, BTCUSD)

Any MT5 broker should work due to the automatic symbol resolution. If a symbol cannot be resolved, the signal for that account will show an error in `trade_queue` and the trade will be skipped.
