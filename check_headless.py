import subprocess

# Check if fix is on operator
result = subprocess.run(['ssh', 'operator@192.0.2.21', 
                        'grep "is_headless" ~/market-bot/market-pie5-bot/main.py'],
                       capture_output=True, text=True, timeout=10)

if result.stdout:
    print("✓ Headless mode code found on operator")
    print(result.stdout[:200])
else:
    print("✗ Headless mode code NOT found on operator")
    print("Need to redeploy code")
    
    # Pull latest code
    print("\nPulling latest code...")
    subprocess.run(['ssh', 'operator@192.0.2.21',
                   'cd ~/market-bot/market-pie5-bot && git pull origin copilot/integrate-batch-pricing'],
                  timeout=15)
    
    # Kill old bot
    print("Killing old bot process...")
    subprocess.run(['ssh', 'operator@192.0.2.21', 'pkill -f "python main.py"'], 
                  timeout=10)
