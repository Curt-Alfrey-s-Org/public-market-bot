#!/usr/bin/env python3
"""
Debug script to test API connection and identify issues
"""

import sys
import socket
import requests
from urllib.parse import urlparse

def test_port(host, port):
    """Test if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error testing port {port}: {e}")
        return False

def test_api_connection():
    """Test API connection"""
    print("=" * 60)
    print("API Connection Debug")
    print("=" * 60)
    
    # Test 1: Port availability
    print("\n1. Testing port 8000...")
    if test_port("localhost", 8000):
        print("   ✓ Port 8000 is open")
    else:
        print("   ✗ Port 8000 is not accessible")
        print("   → API server may not be running or bound incorrectly")
        return False
    
    # Test 2: HTTP connection
    print("\n2. Testing HTTP connection...")
    try:
        response = requests.get("http://localhost:8000/", timeout=3)
        print(f"   ✓ HTTP connection successful (status: {response.status_code})")
        print(f"   Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("   ✗ Cannot connect to API")
        print("   → Check if uvicorn is running: ps aux | grep uvicorn")
        return False
    except Exception as e:
        print(f"   ✗ Connection error: {e}")
        return False
    
    # Test 3: Health endpoint
    print("\n3. Testing /api/health endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=3)
        if response.status_code == 200:
            print(f"   ✓ Health check passed: {response.json()}")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Health check error: {e}")
        return False
    
    # Test 4: CORS headers
    print("\n4. Testing CORS configuration...")
    try:
        response = requests.options(
            "http://localhost:8000/api/health",
            headers={"Origin": "http://localhost:5173"}
        )
        cors_header = response.headers.get("access-control-allow-origin")
        if cors_header:
            print(f"   ✓ CORS configured: {cors_header}")
        else:
            print("   ⚠ CORS header not found")
    except Exception as e:
        print(f"   ⚠ CORS test error: {e}")
    
    # Test 5: Bot status endpoint
    print("\n5. Testing /api/bot/status endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/bot/status", timeout=3)
        if response.status_code == 200:
            print(f"   ✓ Bot status: {response.json()}")
        elif response.status_code == 503:
            print("   ⚠ Bot status: 503 (bot instance not available - expected)")
        else:
            print(f"   ✗ Bot status failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Bot status error: {e}")
    
    print("\n" + "=" * 60)
    print("Debug Complete")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_api_connection()
    sys.exit(0 if success else 1)
