import subprocess
import time

print("Pulling latest code on operator...")
subprocess.run(['ssh', 'operator@192.0.2.21', 
                'cd ~/market-bot/market-pie5-bot && git pull origin copilot/integrate-batch-pricing'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)

print("Killing old bot processes...")
subprocess.run(['ssh', 'operator@192.0.2.21', 'pkill -9 -f "python main.py"'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)

time.sleep(2)

print("Starting bot in yfinance mode (headless, should auto-start)...")
subprocess.Popen(['ssh', 'operator@192.0.2.21', 
                 'nohup bash -c "cd ~/market-bot/market-pie5-bot && export PAPER_TRADING_MODE=true && export SCHWAB_SANDBOX_MODE=false && source venv/bin/activate && python main.py" > /tmp/bot.log 2>&1 &'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Waiting 10 seconds for bot startup...")
time.sleep(10)

print("\nChecking bot process...")
result = subprocess.run(['ssh', 'operator@192.0.2.21', 'ps aux | grep python | grep main.py | grep -v grep'],
                       capture_output=True, text=True, timeout=10)
if result.stdout:
    print(f"✓ Bot process running:\n{result.stdout}")
else:
    print("✗ Bot process not found - check /tmp/bot.log")

# Show last lines of bot log
print("\nBot log (last 20 lines):")
result = subprocess.run(['ssh', 'operator@192.0.2.21', 'tail -20 /tmp/bot.log'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10)
print(result.stdout if result.stdout else "(empty)")
