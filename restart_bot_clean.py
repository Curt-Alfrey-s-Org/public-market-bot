import subprocess
import time

print("Checking running bot processes...")
result = subprocess.run(['ssh', 'operator@192.0.2.21', 'ps aux | grep "python main.py"'],
                       capture_output=True, text=True, timeout=10)

processes = [line for line in result.stdout.split('\n') if line and 'grep' not in line]
print(f"Found {len(processes)} python main.py processes:")
for proc in processes:
    print(f"  {proc[:150]}")

if processes:
    print("\nKilling all python main.py processes...")
    subprocess.run(['ssh', 'operator@192.0.2.21', 'pkill -9 -f "python main.py"'], timeout=10)
    time.sleep(2)

print("\nStarting fresh bot with proper environment...")
cmd = ('cd ~/market-bot/market-pie5-bot && '
       'export PAPER_TRADING_MODE=true && '
       'export SCHWAB_SANDBOX_MODE=false && '
       'source venv/bin/activate && '
       'nohup python main.py > bot_startup.log 2>&1 &')

subprocess.run(['ssh', 'operator@192.0.2.21', cmd], timeout=10)

print("Waiting 10 seconds for bot to start...")
time.sleep(10)

# Check if bot is running
result = subprocess.run(['ssh', 'operator@192.0.2.21', 'pgrep -f "python main.py" | wc -l'],
                       capture_output=True, text=True, timeout=10)
count = result.stdout.strip()
print(f"Bot processes running: {count}")

# Check startup log
print("\nBot startup output:")
result = subprocess.run(['ssh', 'operator@192.0.2.21', 'tail -30 bot_startup.log'],
                       capture_output=True, text=True, timeout=10)
print(result.stdout)
