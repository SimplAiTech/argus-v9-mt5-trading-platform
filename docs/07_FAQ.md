# ARGUS V9 — Frequently Asked Questions

---

## General

**Q: Does ARGUS work on Mac or Linux?**  
A: No. The MetaTrader 5 Python API (`MetaTrader5` package) is Windows-only. ARGUS requires Windows 10 or 11.

**Q: Do I need MetaTrader 5 open all the time?**  
A: Yes. ARGUS connects to the MT5 application running on your PC. MT5 must remain open for ARGUS to fetch data and execute trades. If MT5 closes, ARGUS will stop trading and log connection errors.

**Q: Can I run ARGUS on a VPS?**  
A: Yes, as long as it's a Windows VPS. A 4 GB RAM, 2-core VPS is sufficient for running both MT5 and ARGUS. Cloud VPS providers with Windows support (e.g., Contabo, Vultr, AWS EC2 Windows) work well.

**Q: What happens to open trades if I close ARGUS?**  
A: Open positions remain active in MT5 and will be managed by MT5's own stop orders. ScaleOut and any automatic management will not run until ARGUS is restarted.

---

## Accounts & Brokers

**Q: How many accounts can I run simultaneously?**  
A: There is no hard limit. ARGUS handles multiple accounts through one MT5 terminal by switching between them. Practically, 3–5 accounts per terminal run comfortably. More accounts increase the switching cycle time.

**Q: My broker uses a different symbol name (e.g., GOLD instead of XAUUSD). Will ARGUS work?**  
A: Usually yes. ARGUS has automatic symbol resolution that tries: direct match, alias map, suffix probing (.PRO, .raw, etc.), and substring matching. If ARGUS cannot resolve a symbol for your broker, the trade for that instrument will be skipped and an error logged. Contact support with your broker's symbol list to add it to the alias map.

**Q: Does ARGUS support cTrader, NinjaTrader, or other platforms?**  
A: Currently ARGUS supports MT5 only. NinjaTrader support is in development (V10 roadmap). The `platform` field in `trading_accounts` accepts `'NINJA'` but execution is not yet implemented.

**Q: Can I add the same MT5 account twice?**  
A: You can have the same account on multiple ARGUS user profiles, but adding it twice under the same user will cause duplicate execution of signals on that account.

---

## Trading & Signals

**Q: Why is ARGUS not generating any signals?**  
A: Check the following:
1. AutoFlow is enabled (toggle in the top bar)
2. At least one strategy is enabled (Strategies tab)
3. MT5 is connected and Algo Trading is enabled
4. The Logs tab shows no critical errors (HARD_STOP, connection failure)
5. Check if the AI confidence threshold is too high in `config.json` (`ai_min_confidence`)

**Q: How often does ARGUS scan the market?**  
A: BrainEngine runs a full scan cycle every **30 seconds**. Each cycle analyzes all active symbol/timeframe combinations simultaneously.

**Q: Can I trade with ARGUS manually at the same time?**  
A: Yes. ARGUS only manages trades that it opened (tracked by ticket in `positions_realtime`). Manually opened trades in MT5 will not be touched by ARGUS's ScaleOut or other management functions.

**Q: ARGUS opened a trade without a Stop Loss. What happened?**  
A: This can happen with BTCUSD or ETHUSD when the calculated SL is too small for the broker's minimum stop distance. ARGUS now enforces a minimum SL of 0.3% of the current price for instruments above $1,000. If you see trades without SL on older versions, update to the latest release.

**Q: How do I stop ARGUS from trading a specific instrument?**  
A: In the **Strategies** tab, find each strategy that trades that instrument and either disable the strategy entirely, or reduce its `max_trades_per_day` to 0 for that instrument. A more granular per-symbol disable is planned for a future release.

---

## Risk & Performance

**Q: What is a "HARD_STOP_DRAWDOWN" error?**  
A: This means your account's equity has dropped to or below the maximum drawdown floor you configured. ARGUS stops generating new signals for this account as a protective measure. Review your open positions, close losing trades if needed, and reset the account status in the Accounts tab to resume.

**Q: ARGUS keeps showing "DAILY_LIMIT_REACHED". How do I reset it?**  
A: The daily limit resets automatically at midnight UTC. If you need to trade before midnight, you can temporarily increase `daily_loss_limit_usd` in the account settings, but only if your prop firm rules allow it.

**Q: What does the AI confidence score mean? Can I change the threshold?**  
A: The AI model assigns each signal a probability that it will be profitable (0 = certain loss, 1 = certain win). The default threshold of 0.40 was chosen based on the model's live performance (AUC=0.77). You can change it in `config.json` under `ai_settings.min_confidence`. Setting it below 0.30 is not recommended; above 0.55 will filter out most signals.

**Q: Why does ARGUS sometimes skip entire brain cycles?**  
A: If MultiAccountEngine is currently logged into a secondary account, BrainEngine detects this and silently skips the cycle. This is by design — fetching data from the wrong account would return meaningless results. At most one 30-second cycle is skipped per account switch.

---

## Telegram Bot

**Q: The Telegram `/status` command doesn't work.**  
A: The bot command is handled by a Supabase Edge Function and does not require ARGUS to be running. If `/status` doesn't respond:
1. Make sure you completed the connection setup (Settings → Notifications → Connect Bot)
2. Try `/start` again in the bot chat — this re-links your chat ID
3. Check that your MT5 login was entered correctly during the `/start` flow

**Q: Can multiple accounts notify the same Telegram chat?**  
A: Yes. If multiple MT5 accounts are linked to the same Supabase user, the `/status` command shows the primary account in detail and lists all others with their balance/equity.

**Q: I'm not getting trade notifications anymore.**  
A: Trade notifications are sent by ARGUS_TERMINAL when it executes a trade. Ensure ARGUS is running. If you recently re-connected Telegram, the chat ID may have changed — go to Settings → Notifications → Connect Bot and reconnect.

---

## Installation & Updates

**Q: I get `ModuleNotFoundError` when starting ARGUS.**  
A: Run `pip install -r requirements.txt` again. If a specific module fails to install, try installing it manually: `pip install <module-name>`. Make sure you're using Python 3.10+.

**Q: How do I update ARGUS to a new version?**  
A: Replace the ARGUS folder contents with the new release package. Your `.env` file and `config.json` customizations will be overwritten — back them up first. The database (Supabase) is cloud-hosted and does not need to be updated locally.

**Q: Can I have multiple ARGUS installations on the same PC?**  
A: Yes, but only one instance should run at a time per MT5 terminal. Running two ARGUS instances against the same MT5 will cause execution conflicts. If you need to run two instances, use two separate MT5 terminals (e.g., one demo, one live).

---

## Data & Privacy

**Q: Where is my trading data stored?**  
A: All data (accounts, signals, trade history, positions) is stored in Supabase (PostgreSQL cloud database). MT5 credentials are stored encrypted in Supabase and are only used to connect to your broker's MT5 server.

**Q: Who can see my data?**  
A: Row Level Security (RLS) in Supabase ensures each user can only access their own data. The system administrator (ARGUS provider) can access all data via the service key, which is not distributed to users.

**Q: Can I export my trade history?**  
A: Yes — from the **History** tab in ARGUS, use the export button to download your trade log as a CSV file. Full analytics are available in the **Analytics** tab.
