# Today’s Best Discovery: Continuous, Ranked, Don’t Stop Looking

This doc describes how the bot should pick **today’s** best stocks (highest win probability, most profitable) and **keep looking** even after it’s trading a fixed number of names.

**Relationship to [ROADMAP.md](../ROADMAP.md):** This aligns with **Roadmap Idea #2 (Top performers / popular symbols feed)** and **§4e (Resource efficiency when list full)**. Roadmap #2 defines Feed → watchlist → screener and live updates; the mechanism below (periodic symbol-list refresh in the bot loop) is **complementary**: it keeps the **screener** list fresh when the API loop uses the screener. Same goal (today’s best, don’t stop looking); works alongside the existing Top Performers Feed.

---

## What we want

1. **Today’s stocks with highest probability of winning and most profitable**  
   Rank and trade by **current** win probability and profitability potential, not a static or yesterday’s list.

2. **Not just symbols stored**  
   The bot should use **metrics** (win probability, composite score, profitability) to rank and choose, not just a list of tickers. It can keep yesterday’s winners in the pool but **re-rank** by today’s data.

3. **Bot must keep looking at other stocks**  
   It must not lock into a one-time list and never re-scan. It should **periodically re-run discovery** so “today’s best” and “hot stock 10 minutes from now” can enter the pool.

4. **Yesterday’s winners ≠ best today**  
   Storing yesterday’s winners is fine as candidates, but **today’s** screening/ranking should decide who is best **today**. No guarantee yesterday’s winners stay on top.

5. **Don’t quit looking when we hit N positions**  
   Hitting “max positions” or “max symbols to trade” only limits **how many** we can hold or trade. The bot should **keep scanning** the full candidate set every cycle (or every N cycles). If a hot stock appears later, it can enter the list and compete for a slot (e.g. we might close a colder position for a hotter one in a future enhancement).

---

## Current behavior (before this design)

- **Symbols loaded once** at bot start via `load_scan_symbols()` (screener or file).
- **Same list every cycle:** the loop always iterates over that initial list; it is **never** refreshed.
- **“Popular” fallback** is the first N symbols of the universe (alphabetical), not “best today.”
- **Max positions** only blocks opening new positions; the bot still iterates over the full list, but that list is fixed at startup.

So the bot **does** keep “looking” at every symbol in its list each cycle, but the **list itself** is stale (one-time load, possibly cached universe). A “hot stock 10 min from now” never enters the list unless we refresh it.

---

## Target behavior

1. **Periodic re-discovery**  
   Re-run the screener (or equivalent) on an interval (e.g. every 1 cycle, or every N cycles, or every T seconds). Refresh the **symbol list** the bot uses so it’s “today’s best” (ranked by current screener output: composite score, win probability, etc.).

2. **Rank by today’s metrics**  
   When the screener runs, it uses **current** price, volume, volatility, and (if enabled) sentiment/ML. The returned list is ordered by **current** composite score / win probability. So “today’s best” = top of that list. No reliance on “yesterday’s list” except as a candidate pool that gets re-ranked.

3. **Store more than symbols (roadmap)**  
   Ideally we keep **symbol + score + win_prob** (and maybe profitability proxy) so the bot and UI can show “why” a symbol is on the list. The screener already computes these; we can persist or pass them through instead of dropping to “just symbols.”

4. **Never stop looking**  
   Even when at max positions, the bot still iterates over the **full refreshed candidate list** each cycle. It evaluates every candidate; it just can’t open more than N positions. So a “hot stock 10 min from now” appears in the next refresh and gets evaluated; future work can add “replace cold position with hot” logic.

5. **Backward compatibility**  
   If we don’t want periodic refresh (e.g. to avoid screener load), we keep **load once at startup** as the default. An env var (e.g. `SYMBOL_REFRESH_INTERVAL_CYCLES`) controls how often we refresh (0 = only at startup, 1 = every cycle, N = every N cycles).

---

## Implementation (done / planned)

- **SYMBOL_REFRESH_INTERVAL_CYCLES** (env):  
  - `0` (default): load symbols once at startup (current behavior).  
  - `1`: refresh symbol list every trading cycle (today’s best every cycle).  
  - `N`: refresh every N cycles.  
  Set to `1` (or another value) in `.env` to have the bot keep re-discovering “today’s best” and pick up hot stocks that appear later.

- In the **bot loop** (e.g. API bot manager):  
  At the start of each cycle, if `SYMBOL_REFRESH_INTERVAL_CYCLES > 0` and `(cycle_count % SYMBOL_REFRESH_INTERVAL_CYCLES == 0)`, call `load_scan_symbols(...)` again and set `bot.current_symbols` (and the list the loop iterates over) to the new list. Log something like: “Refreshed symbol list (today’s best): N symbols.”

- The **for-loop** continues to iterate over the **current** list (the one we just refreshed when applicable). So after a refresh, the next cycle uses the new “today’s best” order and can include a newly hot symbol.

- **Screener** already returns symbols **ranked** by composite score / win probability when it runs. So each refresh gives “today’s best” order; we don’t need a separate “yesterday’s winners” list unless we explicitly want to merge it into the candidate pool and re-rank (future enhancement).

- **Roadmap:**  
  - Persist or pass **symbol + score + win_prob** (and optional profitability proxy) so the bot doesn’t “just store symbols.”  
  - Optional: “Replace cold position with hot” when at max positions and a new candidate ranks higher than an existing position.

---

## Summary

- We want **today’s** stocks with **highest win probability** and **most profitable**, not a static or yesterday-only list.
- We should **not** rely on “just symbols stored”; we should use **today’s** metrics to rank and, over time, store scores with symbols.
- The bot must **not** stop looking: it should **periodically re-run discovery** and always iterate over the **full current candidate list** each cycle, even at max positions, so a hot stock 10 minutes from now can show up and be considered.
- **SYMBOL_REFRESH_INTERVAL_CYCLES** controls how often we refresh that list (0 = once at startup, 1 = every cycle, N = every N cycles).

**Implementation status:** In `api/bot_manager.py`, **`_load_symbols_todays_best()`** implements Feed → screener/file priority. It is used at startup and on every refresh when `SYMBOL_REFRESH_INTERVAL_CYCLES > 0`. If the Top Performers Feed is empty (e.g. not yet populated), the bot uses the screener or file.
