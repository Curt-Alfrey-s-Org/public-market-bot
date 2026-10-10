# Mission: market-pie5-bot

**Last Updated:** January 24, 2026  
**Status:** Canonical mission and production scope

---

## Mission Statement

**The bot exists to automate stock and options trading:**

1. **Phase 1 — Stocks (production first):** Trade stocks via **buy** (long) and **short** (short) positions. Achieve production-ready, reliable stock trading before expanding scope.
2. **Phase 2 — Options (after stocks):** Integrate **options** trading once Phase 1 stock trading is complete and validated.

---

## Phase 1: Stock Trading (Buy & Short)

### Scope

- **Long positions:** Open with BUY, close with SELL. Full lifecycle, risk controls, and reporting.
- **Short positions:** Open with SHORT, close with COVER. Same rigor as longs: margin/short-availability checks, buy-in risk, reporting.

### Production-Ready Definition (Phase 1)

Phase 1 is “production-ready” when:

- [ ] **Buy (long)** — Implemented, tested, and documented for paper and live use.
- [ ] **Short** — Implemented, tested, and documented for paper and live use.
- [ ] **Unified position model** — All positions tracked with `side` (long/short); risk, P&L, and tax logic respect side.
- [ ] **Strategies** — Can signal BUY, SELL, SHORT, COVER (or equivalent) where applicable.
- [ ] **Order types** — Work for both longs and shorts (e.g. trailing stops for shorts already partially supported in `order_types.py`).
- [ ] **Broker integration** — Schwab (or configured broker) supports the required order types and short selling.
- [ ] **Validation** — Extended paper/sandbox runs, basic load and failure testing, no known critical bugs for stock flow.
- [ ] **Docs & ops** — Setup, config, and runbooks sufficient for a careful operator to run in production.

---

## Phase 2: Options Trading (After Stocks)

### Scope

- Options chain data, pricing, Greeks.
- Single-leg and later multi-leg strategies as needed.
- Integration with existing risk, logging, and reporting.

### Timing

- **Start:** Only after Phase 1 (stocks buy/short) is production-ready and stable.
- **Dependencies:** Stock trading proven in paper/live; architecture and ops process in place.

---

## Current State vs Mission

### Phase 1 (Stocks)

| Capability | Status | Notes |
|------------|--------|-------|
| **Buy (long)** | ✅ Implemented | BUY opens, SELL closes. Position tracking, trailing stops, filters, T+1, PDT. |
| **Short** | ❌ Not implemented | No SHORT/COVER in `execute_trade`. Strategies are BUY/SELL/HOLD only. `order_types` has trailing-stop logic for “buy to cover” but it’s not wired into the main loop. |
| **Unified position model** | ⚠️ Long-only | Positions stored without `side`. No short-specific tracking or risk. |
| **Strategies** | ⚠️ Long-only | SMA, Bollinger, RSI, MACD, Momentum: BUY/SELL/HOLD only. |
| **Order types** | ⚠️ Partial | Trailing stops etc. support short concepts; execution path is long-only. |

### Phase 2 (Options)

| Capability | Status | Notes |
|------------|--------|-------|
| **Options** | ❌ Not started | Explicitly Phase 2. Framework ideas exist; no options implementation. |

---

## Production Readiness Checklist (Phase 1)

Use this to track progress toward “production-ready” stock trading.

### 1. Core Trading

- [x] BUY/SELL (long) — open, hold, close with filters and risk checks.
- [x] SHORT/COVER — open, hold, close in execute_trade (paper + live); margin/availability + concentration checks via `can_open_short`.
- [x] Position `side` — every position has long/short; all downstream logic uses it.
- [x] Strategies — BUY/SELL/HOLD wired into CLI + GUI; **(signal, position)→action** mapping (SELL+flat→SHORT, BUY+short→COVER) enables shorts without strategy SHORT/COVER.

### 2. Risk & Compliance

- [x] PDT handling for longs (and shorts where applicable).
- [x] T+1 settlement for cash accounts.
- [x] Margin/short-availability checks before opening shorts (`can_open_short`, env gates).
- [x] Capital floor, position limits, trailing stops for longs.
- [x] Short concentration limits (max positions, max exposure %). Buy-in risk deferred.

### 3. Broker & Infrastructure

- [x] Schwab API (paper + live) for stock orders.
- [ ] Confirm Schwab short-selling support and order types for shorts.
- [x] Paper and sandbox modes for testing.

### 4. Validation & Ops

- [ ] Extended paper/sandbox runs (e.g. 30+ days) with buy+short.
- [ ] Basic failure testing (e.g. API outages, network blips).
- [ ] Runbooks for deployment, config, and common failures.

### 5. Documentation

- [ ] Mission and phases (this doc) linked from README, PROJECT_STATUS, ROADMAP.
- [ ] Short-selling design and config documented.
- [ ] Production checklist and gap analysis updated as work completes.

---

## How This Doc Is Used

- **Planning:** ROADMAP and PROJECT_STATUS should align with Phase 1 (stocks) then Phase 2 (options).
- **Design:** New features (e.g. short selling, options) should reference MISSION and the relevant phase.
- **Production:** Before going live, validate against the Phase 1 checklist and close known gaps.

---

## Summary

| Phase | Focus | Production-ready when |
|-------|--------|------------------------|
| **1** | Stocks: buy + short | Both long and short flows implemented, tested, documented, and validated. |
| **2** | Options | Phase 1 complete; then options integrated and validated. |

**Next steps:** Implement short selling (SHORT/COVER, position side, strategies, risk), then complete the Phase 1 checklist and validation. Options work begins only after Phase 1 is production-ready.
