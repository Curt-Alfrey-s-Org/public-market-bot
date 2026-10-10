# Current task for GitHub Copilot

**Updated:** 2026-01-25  
**Branch:** `copilot/update-documentation-index`  
**Scope:** One file only — `DOCUMENTATION_INDEX.md`. No code or other docs.

---

## Task: Update DOCUMENTATION_INDEX with missing entries

Several docs and resources exist but are **not** listed in [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md). Add them so users can discover them.

**Do this:**

1. **Add [EMAIL_ALERTS_GUIDE.md](EMAIL_ALERTS_GUIDE.md)**  
   - Place under **Security & Configuration** (same section as TOKEN_ENCRYPTION_GUIDE, ENV_SIMPLIFICATION, etc.).  
   - Description: email alert setup (SMTP, Gmail, Outlook), `demo_email_alert.py` test, troubleshooting.

2. **Add [debug_logs/README.md](debug_logs/README.md)**  
   - Place under **Developer Documentation** → **Development Guides** (or a short "Debug & tooling" subsection if you prefer).  
   - Description: Linux-captured debug logs pushed for Cursor analysis; numbered scripts `run_linux_commands_2.sh`, `_3.sh`, … write `debug_logs/run_N_*` (no overwriting). See also [DEV_DEPLOY_WORKFLOW.md](DEV_DEPLOY_WORKFLOW.md) "Debug logs for Cursor."

3. **Refresh [DEV_DEPLOY_WORKFLOW.md](DEV_DEPLOY_WORKFLOW.md) row** in **Essential Documents**  
   - Extend the Purpose column to mention: "Git workflow, line endings, **Linux commands script**, **debug logs for Cursor**."  
   - Keep the rest of the row unchanged.

4. **Update "Last Updated"** at the top of `DOCUMENTATION_INDEX.md` to the current date (e.g. `January 25, 2026`).

**Do not:**

- Change any other files (no .env, no code, no other docs).
- Remove or reorder existing entries except as needed to fit new ones logically.
- Edit the actual content of EMAIL_ALERTS_GUIDE, debug_logs/README, or DEV_DEPLOY_WORKFLOW.

**Acceptance criteria:**

- [ ] `EMAIL_ALERTS_GUIDE.md` is listed under Security & Configuration with a brief, accurate description.
- [ ] `debug_logs/README.md` is listed under Developer Documentation with a brief, accurate description.
- [ ] `DEV_DEPLOY_WORKFLOW.md` Essential Documents row mentions "debug logs for Cursor" (and optionally "Linux commands script").
- [ ] "Last Updated" is set to the date you make the edits.
- [ ] Links are valid (relative paths like `EMAIL_ALERTS_GUIDE.md`, `debug_logs/README.md`, `DEV_DEPLOY_WORKFLOW.md`).

**Workflow:**

1. Create branch `copilot/update-documentation-index`.
2. Edit **only** `DOCUMENTATION_INDEX.md`.
3. Open a PR. When done, add the `copilot-completed` label so Copilot Sentinel passes.

---

*When this task is done, update this file with the next scoped task or replace it with "No current task."*
