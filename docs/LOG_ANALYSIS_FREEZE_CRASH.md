# Log Analysis: Bot Froze Screen & Crashed to Login (Linux Mint)

## What You Reported
- The bot **froze the screen** and **crashed back to the login screen** on Linux Mint.
- “Login screen” = Linux Mint display manager (GDM/sddm), i.e. the **whole desktop session** ended.

---

## 1. Logs Searched

| Source | Path | Contents |
|--------|------|----------|
| **Bot log** | `trading_bot.log` | Main bot, API, throttling, alerts, errors |
| **Alerts** | `alerts.log` | Alert subjects/bodies (email-style) |
| **Debug** | `debug_logs/*.txt` | Env info, run results, screener |

---

## 2. Findings from `trading_bot.log`

### 2.1 Shutdown / Context Errors (Repeated)
```
Error during shutdown: Working outside of request context.
werkzeug.server.shutdown not available, using os._exit()
Application shutdown initiated by user
```
- **Meaning:** When you stop the app (e.g. Stop button), shutdown runs from a **background thread** and uses Flask/Dash `request` outside an HTTP request → “Working outside of request context.”
- The app then falls back to **`os._exit()`** (immediate process kill, no cleanup).
- **Impact:** Messy shutdown. Unlikely to **by itself** kill the whole session, but worth fixing.

### 2.2 Resource Throttling
```
Resource throttling enabled: CPU<75.0%, Memory<75.0%, Disk<90.0%, Network<100.0MB/s
Resource throttling disabled by configuration
```
- When **enabled**, the bot slows down (CPU/memory throttle) to avoid overload.
- When **disabled**, there is no in-process limit; the bot can use more CPU/RAM.

### 2.3 Heavy Workload (Screening)
```
SCREENING TIMING BREAKDOWN (total: 26.14s)
Phase 1 (fetch+filter): 26.14s — 16 filtered from 158 fetched
Screening complete: 16/156 stocks passed filters
```
- **~26s** screening runs, **158 stocks** fetched, ML/sentiment on top.
- This can **spike CPU and memory**, especially on constrained hardware (e.g. Pi 5, low-RAM laptop).

### 2.4 “Trading Paused - T+1 Settlement” Alert Storm
```
main - CRITICAL - ALERT - [CRITICAL] Subject: Trading Paused - T+1 Settlement
```
- Many such **CRITICAL** alerts in a short window (e.g. 17:58–17:59 on 2026-01-26).
- Occurs when **all capital is unsettled** (T+1) and **every** trade attempt is skipped.
- **Impact:** If each skip triggers an alert, you get an **alert storm** (logging, optional email, GUI updates). That can add CPU/memory and I/O load during an already busy period.

### 2.5 Other Errors (Not Direct Cause of Session Crash)
- **Schwab API** failures (live mode, credentials/token).
- **Failed to decrypt value** (env/token decryption).
- **NewsAPI / Finnhub** 401 (invalid API keys).
- **SMTP** auth failures (e.g. Gmail “Username and Password not accepted”).
- **yfinance** “possibly delisted” for some symbols (e.g. HES, MRO).

These affect trading/alerts but are not proof of **display/session** crash.

---

## 3. Why “Freeze + Crash to Login” Usually Happens (System-Level)

When the **entire session** dies and you end up at the **Linux Mint login** again, typical causes are:

| Cause | What to look for |
|-------|-------------------|
| **OOM (Out of Memory)** | Kernel kills processes (often the biggest memory users). Sometimes the compositor/display manager goes too → session gone. |
| **GPU / graphics driver crash** | Compositor or X/Wayland dies → freeze then drop to login. |
| **X11/Wayland compositor crash** | Same result: session ends, back to login. |

The **bot logs** do **not** contain OOM or GPU crash messages. Those show up in **system** logs, not `trading_bot.log`.

---

## 4. How the Bot Can Contribute

1. **CPU/memory use**
   - Screening (158 stocks, ~26s), ML, sentiment, etc.
   - If **resource throttling is off**, the bot does not slow itself down under load.

2. **Alert storm**
   - Many “Trading Paused - T+1 Settlement” CRITICAL alerts in a short time.
   - Extra logging, file I/O, optional email, and GUI updates → more load when the system is already busy.

3. **Shutdown path**
   - `os._exit()` is abrupt. Unlikely to kill the session by itself, but the shutdown sequence is not clean.

---

## 5. What to Do Next

### 5.1 Check **System** Logs (Important)

**OOM / process kills:**
```bash
# Recent kernel messages (OOM, kills)
journalctl -k -b -1 --no-pager | grep -iE 'oom|kill|out of memory|invoked oom'

# Or syslog
grep -iE 'oom|kill|out of memory' /var/log/syslog
```

**General failures around the time of the freeze:**
```bash
journalctl -b -1 --since "2026-01-26 17:55" --until "2026-01-26 18:05" --no-pager
```
- Adjust date/time to when the freeze happened.
- Look for OOM, GPU, Xorg/Wayland, compositor, or desktop-session errors.

### 5.2 Reduce Bot-Side Load (Mitigations)

1. **Turn resource throttling on**  
   - In Settings → Advanced (or .env):  
     `BOT_ENABLE_THROTTLING=true`  
   - Keeps CPU/memory below configured limits.

2. **Lower screening load**  
   - Reduce `MAX_STOCKS_TO_SCAN` / batch size so screening is lighter and shorter.

3. **Avoid T+1 alert storms**  
   - When **all** capital is unsettled, the bot should **not** send a CRITICAL “Trading Paused - T+1 Settlement” on **every** skipped symbol.
   - **Recommendation:** Send at most **one** T+1 “trading paused” alert per cooldown (e.g. 15–30 minutes), and optionally rate-limit in `AlertSystem`.

4. **Optional: use margin mode**  
   - If you use **Settings → Trading → Use margin**, the bot uses **total** capital and does not treat unsettled funds as “no capital.” That can reduce repeated T+1-related skips (and thus alerts) when you’re ok using margin.

### 5.3 Fix Shutdown “Working outside of request context”

- Ensure shutdown logic **does not** use `request` (or other Flask/Dash request-scoped state) from a **background thread**.
- Capture `request.environ.get('werkzeug.server.shutdown')` (or equivalent) **inside** the request that triggers shutdown, then call it from the same request flow (or from a thread that properly pushes a request context), instead of calling it later from an arbitrary thread.
- Use a clean exit path (e.g. `sys.exit(0)` or normal server shutdown) instead of `os._exit()` when possible, so atexit and cleanup run.

---

## 6. Summary

| Finding | Severity | Role in freeze/crash |
|--------|----------|----------------------|
| **OOM / GPU / compositor** (system logs) | **High** | Most likely **direct** cause of “freeze → login” |
| **Heavy screening + no throttling** | Medium | Can push CPU/RAM and **trigger** OOM |
| **T+1 “Trading Paused” alert storm** | Medium | Extra load during stress |
| **Shutdown “request context” + `os._exit`** | Low | Bad shutdown, not session killer |

**Next steps:**  
1. Check **journalctl** / **syslog** for OOM, kills, and graphics/session crashes around the freeze time.  
2. Enable **resource throttling** and **reduce** screening load.  
3. **Rate-limit** or coalesce “Trading Paused - T+1 Settlement” alerts to one per cooldown.  
4. **Fix** shutdown so it doesn’t use request context from a background thread and avoids `os._exit()` where possible.

---

*Generated from `trading_bot.log`, `alerts.log`, and codebase search. Re-run log search after fixes and tune dates/ranges for your incident.*
