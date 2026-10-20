# Development & Deployment Workflow

**Work on Linux via Cursor Remote-SSH (edit, run, commit, push — all on Linux)**

You **SSH into the Linux box** and use **Cursor Remote-SSH** to open the project. Edit, run tests, commit, and push **all on Linux** — no push/pull between Windows and Linux.

---

## Workflow Overview

| Step | Where | What |
|------|--------|-----|
| **1. Connect** | Cursor | **File → Connect to Host** → `user@linux-box`, then **Open Folder** → project dir |
| **2. Edit** | Linux (Cursor Remote-SSH) | Edit code, use terminal in same window |
| **3. Run** | Linux | `source venv/bin/activate`, then `python3` tests, `./start_web_gui.sh`, etc. |
| **4. Commit & push** | Linux | `git add` / `git commit` / `git push` from project root |

**Tests** run on **Linux** (venv). Use `python3` and the project venv.

---

## On Your Linux Box (Primary Development)

- **Cursor Remote-SSH:** Connect to the Linux host, open the project folder. All editing and commands happen there.
- Use **Git** to commit and push from the project root on Linux.
- **Avoid** Windows-specific code: use `pathlib` or `os.path`, `python3`-compatible syntax.
- **`.gitattributes`** enforces LF line endings for `.sh`, `.py`, etc.

### Optional: Pre-commit checks on Linux

```bash
# In project root (you're on Linux)
source venv/bin/activate
pip install -r requirements.txt
flake8 . --max-line-length=127 --exclude=venv,node_modules,.git
black . --check --exclude="venv|node_modules|\.git"
```

Otherwise, rely on **CI** (GitHub Actions) and **tests on Linux** before you run the bot.

---

## On Your Linux Box (Run & Test)

### One-time setup

```bash
cd ~
git clone https://github.com/Curt-Alfrey-s-Org/market-pie5-bot.git
cd market-pie5-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your config (API keys, PAPER_TRADING_MODE, etc.)
```

### Run after updates

```bash
cd ~/market-pie5-bot   # or your project path
git pull   # if you pull from GitHub
source venv/bin/activate

# Run tests (recommended before running the bot)
python3 run_unittest.py
# or
python3 -m pytest test_*.py -v
# or
python3 -m unittest discover -s . -p "test_*.py" -v

**When to run which tests (fewer full runs):**
- **Quick validation** (run often while iterating):  
  `python3 -m unittest test_order_type_configuration test_strategy_signals test_short_selling test_order_payload_builder -v`  
  Fast feedback; use after small changes.
- **Full suite** (run less often):  
  `python3 run_unittest.py 2>&1 | tee test_results.txt`  
  Use before PR, after pulling major changes, or periodically. **`run_unittest.py`** sets the pandas/yfinance `Timestamp.utcnow` (Pandas4Warning) filter **before** any imports, then runs `unittest discover`; output stays shorter. Alternatively: `python3 -m unittest discover -s . -p "test_*.py" -v` (filters in `main`/`web_gui`/`data_fetcher`/`async_data_fetcher` may still leave some warnings depending on import order).

# Start the bot
./start_web_gui.sh
# or
./start_bot.sh
# or
./venv/bin/python3 main.py
```

### Using the venv without activating

```bash
./venv/bin/python3 main.py
./venv/bin/python3 -m pytest test_short_selling.py -v
```

---

## Linux commands script

We use **numbered scripts** so each run has its own outputs (no overwriting):

| Script | Purpose |
|--------|---------|
| **`run_linux_commands_2.sh`** | Short-selling validation → `debug_logs/run_2_*` |
| **`run_linux_commands_3.sh`** | Screener test → `debug_logs/run_3_*` |
| **`run_linux_commands_4.sh`**, … | Future workflows → `debug_logs/run_4_*`, … |

On Linux, from project root:

```bash
bash scripts/run_linux_commands_2.sh   # short-validation
bash scripts/run_linux_commands_3.sh   # screener
```

Use `bash scripts/...` so you don't need `chmod +x`. **Do not use sudo** — the script uses git and your venv; sudo can cause "command not found" and path issues. When Cursor gives new "Commands to run" for Linux, it may add **`run_linux_commands_N.sh`** (next N) instead of overwriting.

---

## Debug logs (Linux, local)

Numbered scripts write to **`debug_logs/run_N_env_info.txt`** and **`debug_logs/run_N_results.txt`** (e.g. run 2 = short-validation, run 3 = screener). You're on Linux via Cursor Remote-SSH, so **open those files directly** in Cursor — no pull on another machine. Optionally `git add debug_logs/` + `commit` + `push` for backup.

See **`debug_logs/README.md`** and **`docs/SCREENER_TEST_ANALYSIS.md`** for details.

---

## Line Endings and `.gitattributes`

- **`.gitattributes`** forces LF for `*.sh`, `*.py`, and other text files.
- Prevents **CRLF** (Windows) from breaking scripts on Linux (e.g. `bad interpreter`).
- If you already have CRLF in repo, fix with:
  ```bash
  git add --renormalize .
  git commit -m "Normalize line endings (LF) for Linux"
  ```

---

## Summary

- **Work on Linux** via Cursor Remote-SSH: edit, run, commit, push — all on the same machine.
- **Test** on Linux (venv). **Debug logs** are local; open `debug_logs/run_N_*` in Cursor.
- Use **LF** everywhere; `.gitattributes` handles it.

For installation details on Linux Mint, see [LINUX_MINT_GUIDE.md](LINUX_MINT_GUIDE.md).  
For mission and production scope, see [MISSION.md](MISSION.md).
