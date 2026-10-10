# market-pie5-bot Roadmap

**Last updated:** Jun 2026

---

## Backlog — AI inline doc references (apply later)

Mirror **rankings-bot**: `../rankings-bot/docs/AI_INLINE_DOC_REF_PROCESS.md`.

---

## Next step (planned): research + audit subagent pass

Run the two-stage subagent workflow developed in `alfa-ai/docs/audit/` during the May 2026 ALFa AI architectural audit. The pattern surfaced 64 findings (17 Critical) on alfa-ai; we want the same coverage on every active repo before resuming feature work.

1. **Research Agent** — gathers OFFICIAL upstream docs for every technology this repo uses (versions, security posture, best practices, deprecations). Writes per-component facts + an audit checklist to `docs/audit/research/<component>.md` and a master `docs/audit/research/INDEX.md`.
2. **Audit Agent** — reads the research files, audits this repo against the embedded checklists + cross-cutting checks (internal-doc consistency, stale references, security-currency vs published CVEs, cluster-rules compliance). Writes findings + a severity-ranked remediation backlog to `docs/audit/audit-findings.md`.

Both passes are read-only on the host stack — they only write into the new `docs/audit/` directory. Remediation is gated on explicit per-finding approval.

**Reference workflow:**
- Pattern: `/home/operator/alfa-ai/docs/audit/`
- Research output format: `/home/operator/alfa-ai/docs/audit/research/INDEX.md`
- Audit output format: `/home/operator/alfa-ai/docs/audit/audit-findings.md`

Added 2026-05-13 after the alfa-ai audit proved the pattern at scale.

---

The full roadmap lives in **[docs/ROADMAP.md](docs/ROADMAP.md)**.

## Quick Summary

- **Current priority:** Drive Phase 1 (stocks) to live production — see **Production Readiness
  Plan — June 2026** in [docs/ROADMAP.md](docs/ROADMAP.md) (real-money gate, Python 3.10 EOL,
  passlib/bcrypt fix, frontend toolchain EOL, repo hygiene)
- **Mission:** Phase 1 stocks (buy/short) → Phase 2 options
- **Done:** yfinance mode, ML filter, adaptive learning, self-test, React dashboard, `/api/v1`
  routes, token refresh, startup recovery, Postgres backup/restore scripts

See [docs/ROADMAP.md](docs/ROADMAP.md) for completed phases, planned work, backlog, tech debt, and references.
