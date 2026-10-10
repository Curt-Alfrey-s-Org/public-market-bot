# Trading Terminology (Stock Exchange / Official Terms)

This document defines the terms the bot uses so they align with standard stock exchange and regulatory language (e.g. NASDAQ, NYSE, SEC/Investor.gov).

---

## Positions & Actions

| Term | Definition | Bot usage |
|------|------------|-----------|
| **Long position** | Owning the security; profit when price rises. | Opened by **BUY**. |
| **Short position** | Sold borrowed shares; profit when price falls. Closed by buying back (cover). | Opened by **SHORT**, closed by **COVER**. |
| **BUY** | Buy shares; opens a long position or adds to long. | Action: open long. |
| **SELL** | Sell shares you own; closes (or reduces) a long position. | Action: close long. |
| **SHORT** | Short sell; sell borrowed shares to open a short position. | Action: open short. |
| **COVER** | Buy to close a short position; return borrowed shares to the lender. | Action: close short. |
| **Position** | Your stake in a security (long or short). | Used throughout (e.g. "position held"). |

---

## Signals (Strategy Output)

| Term | Definition | Bot usage |
|------|------------|-----------|
| **Signal** | Suggested direction from strategy/algo (no order yet). | BUY, SELL, HOLD. |
| **HOLD** | No suggested trade; stay flat or keep current position. | Strategy says do nothing. Decision report reason: **Hold** if we own the stock (keep position), **No trade** if we don't (no entry). |

---

## Orders & Execution

| Term | Definition | Bot usage |
|------|------------|-----------|
| **Order** | Instruction to buy or sell (e.g. market or limit). | We send an order; it may fill or fail. |
| **Execution** | Carrying out an order (sending to market). | "Execute trade" = send order. |
| **Fill** | Order matched/executed by the market. | Decision reason: **Filled**. |
| **Order submitted** | Order sent, not yet filled or rejected. | Decision reason before we know result. |
| **Order failed** | Order rejected or not filled (broker/venue/message). | Decision reason when status is error. |
| **Execution error** | Exception or system error during execution. | Decision reason on exception. |

---

## Market Data

| Term | Definition | Bot usage |
|------|------------|-----------|
| **Market data** | Quote (bid/ask), last price, volume. | "No market data" when price/volume missing. |
| **Volume** | Number of shares traded. | Used for size and liquidity. |
| **Data timeout** | Request for data (e.g. quote) did not complete in time. | Decision reason when get_strategy_signal times out. |

---

## Decision Report Reasons (Standardized)

| Reason | Meaning |
|--------|--------|
| **Hold** | Strategy says HOLD and we **own** the stock — keep position (don't sell). |
| **No trade** | Strategy says HOLD and we **don't own** the stock — no entry (don't buy). |
| **No market data** | No price or volume available; skip. |
| **Position held** | Signal was BUY/SELL but we already have a position (no new action this cycle). |
| **Order submitted** | Order sent; outcome (fill/fail) not yet updated. |
| **Filled** | Order was filled (trade executed). |
| **Order failed** | Order rejected or returned error. |
| **Execution error** | Exception during execution. |
| **Data timeout** | Data request (e.g. OHLCV) timed out. |
| **Pending** | Symbol not yet evaluated this cycle. |

---

## Other Terms

| Term | Definition |
|------|------------|
| **Paper trading** | Simulated trading (no real money). |
| **Sandbox** | Broker test environment (e.g. Schwab sandbox). |
| **Symbol** | Ticker (e.g. AAPL). |
| **Cycle** | One pass over the candidate symbols (evaluate each, then wait before next cycle). |
