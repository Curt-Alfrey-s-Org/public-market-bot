#!/usr/bin/env python3
"""
Test Shutdown Server Functionality
Tests what happens when shutdown-server endpoint is called
"""

import requests
import time
import subprocess
import os
import sys

API_URL = "http://localhost:8000"

def check_api_running():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_process_running():
    """Check if uvicorn process is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn api.main:app"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and result.stdout.strip()
    except:
        return False

def main():
    print("=" * 70)
    print("Testing Shutdown Server Functionality")
    print("=" * 70)
    print()
    
    # Check initial state
    print("1. Checking initial state...")
    api_running = check_api_running()
    process_running = check_process_running()
    
    print(f"   API accessible: {api_running}")
    print(f"   Process running: {process_running}")
    print()
    
    if not api_running:
        print("⚠ API is not accessible. Cannot test shutdown.")
        print("   This might be due to permission issues or API not listening.")
        print()
        print("Expected behavior when shutdown-server is called:")
        print("  1. Bot is shut down first")
        print("  2. Response is sent: {'message': 'API server shutdown initiated...', 'status': 'shutting_down'}")
        print("  3. After 1 second, server calls os._exit(0)")
        print("  4. Process terminates (terminal closes if started with ./start_api.sh)")
        print("  5. Frontend shows alerts and disconnects")
        return
    
    # Get bot status before
    print("2. Getting bot status before shutdown...")
    try:
        status_before = requests.get(f"{API_URL}/api/bot/status", timeout=2)
        if status_before.status_code == 200:
            print(f"   Bot status: {status_before.json()}")
        else:
            print(f"   Bot status: HTTP {status_before.status_code}")
    except Exception as e:
        print(f"   Error getting status: {e}")
    print()
    
    # Call shutdown-server endpoint
    print("3. Calling shutdown-server endpoint...")
    try:
        response = requests.post(f"{API_URL}/api/bot/shutdown-server", timeout=5)
        print(f"   Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            print(f"   Message: {data.get('message', 'N/A')}")
        else:
            print(f"   Response: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print("   ⚠ Connection error (expected if server shut down quickly)")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Wait a moment for shutdown
    print("4. Waiting 3 seconds for shutdown to complete...")
    time.sleep(3)
    print()
    
    # Check final state
    print("5. Checking final state...")
    api_running_after = check_api_running()
    process_running_after = check_process_running()
    
    print(f"   API accessible: {api_running_after}")
    print(f"   Process running: {process_running_after}")
    print()
    
    # Results
    print("=" * 70)
    print("Results")
    print("=" * 70)
    
    if not api_running_after and not process_running_after:
        print("✅ SUCCESS: Server was shut down")
        print("   - API is no longer accessible")
        print("   - Process is no longer running")
        print("   - This is the expected behavior")
    elif not api_running_after and process_running_after:
        print("⚠ PARTIAL: API not accessible but process still running")
        print("   - Server might be restarting or there's a permission issue")
    elif api_running_after:
        print("❌ FAIL: Server is still running")
        print("   - Shutdown did not work")
        print("   - Check server logs for errors")
    else:
        print("❓ UNKNOWN: Could not determine state")
    
    print()
    print("Expected Frontend Behavior:")
    print("  1. User clicks 'Shutdown Server' button")
    print("  2. Confirmation dialog: 'Are you sure you want to shutdown...'")
    print("  3. If confirmed, POST request to /api/bot/shutdown-server")
    print("  4. Alert: 'Server is shutting down. The connection will be lost...'")
    print("  5. After 2 seconds, alert: 'Server has been shut down. Please restart...'")
    print("  6. All API queries fail (connection errors)")
    print("  7. User must restart API server manually")

if __name__ == "__main__":
    main()
