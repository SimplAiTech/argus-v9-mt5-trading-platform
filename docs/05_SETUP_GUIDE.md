# ARGUS V9 — Setup Guide

## Requirements

Before starting, ensure you have:

- **Windows 10/11** (MetaTrader 5 Python API is Windows-only)
- **Python 3.10 or higher** — [python.org/downloads](https://www.python.org/downloads/)
- **MetaTrader 5** installed and running
- An active MT5 trading account (demo or funded)
- An ARGUS account (email/password — contact your ARGUS provider)

---

## Step 1: Install Python Dependencies

Open a terminal in the ARGUS folder and run:

```bash
pip install -r requirements.txt
```

This installs all required packages including: `customtkinter`, `MetaTrader5`, `supabase`, `pandas`, `numpy`, `mplfinance`, `scikit-learn`, and others.

> If you see errors about a specific package, install it manually:  
> `pip install <package-name>`

---

## Step 2: Configure Environment (Optional)

ARGUS works out of the box with hardcoded connection defaults. For custom configuration, rename `.env.template` to `.env` and fill in your values:

```env
# MT5 credentials (can also be entered in the GUI)
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_broker_server

# Optional: OpenAI key for LLM news sentiment
OPENAI_API_KEY=sk-...

# Pre-filled — do not change unless instructed
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
TG_BOT_TOKEN=...
```

> The `.env` file is optional. If it doesn't exist, ARGUS uses built-in defaults for Supabase and Telegram. MT5 credentials can always be entered in the GUI instead.

---

## Step 3: Prepare MetaTrader 5

1. Open MetaTrader 5
2. Log in to your trading account
3. Go to **Tools → Options → Expert Advisors**
4. Enable: ✅ **Allow automated trading**
5. Enable: ✅ **Allow DLL imports**
6. Click OK

> MetaTrader 5 must remain open while ARGUS is running.

---

## Step 4: Launch ARGUS

```bash
python ARGUS_TERMINAL.py
```

The ARGUS window will open.

---

## Step 5: Log In

1. On the login screen, enter your **ARGUS email and password**
2. Click **Login**

> These are your Supabase credentials, not your MT5 credentials. You received them from your ARGUS provider.

---

## Step 6: Add Your MT5 Account

1. Go to the **Accounts** tab
2. Click **+ Add Account**
3. Fill in:
   - **MT5 Login** — your account number (e.g., `123456`)
   - **Password** — your MT5 account password
   - **Server** — your broker's server name (e.g., `OxSecurities-Live`, `FundedNext-Server`)
   - **Account Name** — a label for your own reference
   - **Broker** — select or type your broker name
4. Configure risk parameters to match your prop firm rules:
   - **Initial Balance** — the starting balance of your challenge
   - **Max Drawdown ($)** — maximum total drawdown allowed
   - **Daily Loss Limit ($)** — maximum daily loss allowed
   - **Risk per Trade (%)** — default 1.0%
5. Click **Save**

ARGUS will connect to this account and display its balance and equity.

---

## Step 7: Connect Telegram Notifications (Optional)

Receive trade alerts, daily reports, and status updates via Telegram.

1. Go to **Settings → Notifications**
2. Click **Connect Bot**
3. This opens a Magic Link in your browser — click **Open in Telegram**
4. In Telegram, press **START**
5. Your account is now connected

After connecting, you can use these Telegram commands:
- `/status` — current balance, equity, open positions, daily P&L
- `/report` — 7-day performance summary by strategy
- `/report 30` — last 30 days
- `/report today` — today only

---

## Step 8: Enable AutoFlow

1. Ensure MT5 is running and your account is connected
2. Toggle the **AutoFlow** switch in the top bar of ARGUS
3. The status indicator will turn green: `● Algo: MULTI-ACCOUNT RUNNING`

ARGUS is now analyzing the market and will execute trades automatically when valid signals are detected.

---

## Verifying It Works

**Dashboard tab:**  
Should show your account balance, equity, and active strategy count.

**Logs tab:**  
Should show entries like:
```
✅ Supabase client initialized
✅ MT5 connected — Account #123456
✅ BrainEngine started
✅ MultiAccountEngine started
```

**Telegram (if connected):**  
Send `/status` — you should receive a formatted reply with your account details.

---

## Stopping ARGUS

Click the **STOP** button in the top-right corner, or close the window. ARGUS will:
1. Stop BrainEngine (no new signals)
2. Stop MultiAccountEngine (no new executions)
3. Close gracefully — any trades already open remain open in MT5

> Open positions are managed by MT5 itself when ARGUS is not running. No trailing stop or scale-out will occur while ARGUS is stopped.

---

## Troubleshooting

**"MT5 not connected" on startup**  
→ Ensure MetaTrader 5 is open and Algo Trading is enabled in MT5 settings.

**"Login failed" on the ARGUS login screen**  
→ Check your email and password. Contact your ARGUS provider if you don't have credentials.

**No signals being generated**  
→ Ensure AutoFlow is enabled. Check the Logs tab for errors. Verify at least one strategy is enabled in the Strategies tab.

**Trades not executing**  
→ Check that your MT5 account is listed in the Accounts tab with a green status. Verify the account balance is sufficient for minimum lot sizes.

**"No money (10019)" error in logs**  
→ Your account balance is too low for the calculated lot size. Reduce `risk_per_trade_pct` in your account settings, or verify `prop_initial_balance` is set correctly.
