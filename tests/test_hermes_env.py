#!/usr/bin/env python3
"""
Test Hermes Agent Environment Variables
Diagnose if Hermes Agent has proper environment configuration
"""

import os
import sys
import subprocess

def test_hermes_environment():
    """Test Hermes Agent environment variables."""

    print("=== Hermes Agent Environment Test ===")
    print()

    # Test 1: Check environment variables
    print("1. Environment Variables:")
    print(f"   SMTP_SOCKS_PROXY: {os.environ.get('SMTP_SOCKS_PROXY', 'NOT SET')}")
    print(f"   GMAIL_ADDRESS: {os.environ.get('GMAIL_ADDRESS', 'NOT SET')}")
    print(f"   GMAIL_APP_PASSWORD: {'SET' if os.environ.get('GMAIL_APP_PASSWORD') else 'NOT SET'}")
    print()

    # Test 2: Check PySocks availability
    print("2. PySocks Library:")
    try:
        import socks
        print("   [OK] PySocks is available")
        print(f"   Version: {socks.__version__ if hasattr(socks, '__version__') else 'Unknown'}")
    except ImportError:
        print("   [ERROR] PySocks not installed")
        print("   Install with: pip install pysocks")
    print()

    # Test 3: Test SOCKS5 connection
    print("3. SOCKS5 Connection Test:")
    proxy_str = os.environ.get("SMTP_SOCKS_PROXY", "")
    if proxy_str:
        try:
            import socket
            import socks

            proxy_str = proxy_str.replace("socks5://", "")
            if ":" in proxy_str:
                proxy_host, proxy_port = proxy_str.rsplit(":", 1)
                proxy_port = int(proxy_port)
            else:
                proxy_host = proxy_str
                proxy_port = 1080

            sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setproxy(socks.PROXY_TYPE_SOCKS5, proxy_host, proxy_port)
            sock.settimeout(10)
            sock.connect(('smtp.gmail.com', 587))
            print("   [OK] SOCKS5 connection to smtp.gmail.com:587 successful")
            sock.close()
        except Exception as e:
            print(f"   [ERROR] SOCKS5 connection failed: {e}")
    else:
        print("   [SKIP] No proxy configured")
    print()

    # Test 4: Test email sender directly
    print("4. Email Sender Test:")
    email_script = "C:/Users/lanpi/AppData/Local/hermes/skills/academic/email-sender/scripts/send_email.py"
    if os.path.exists(email_script):
        print(f"   Email sender exists: {email_script}")

        # Test with --help
        result = subprocess.run(
            [sys.executable, email_script, "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("   [OK] Email sender script is executable")
        else:
            print(f"   [ERROR] Email sender script failed: {result.stderr}")
    else:
        print(f"   [ERROR] Email sender not found: {email_script}")
    print()

    # Test 5: Recommendations
    print("5. Recommendations:")
    if not os.environ.get("SMTP_SOCKS_PROXY"):
        print("   [WARNING] SMTP_SOCKS_PROXY not set")
        print("   → Set: export SMTP_SOCKS_PROXY=socks5://127.0.0.1:7897")

    if not os.environ.get("GMAIL_ADDRESS"):
        print("   [WARNING] GMAIL_ADDRESS not set")
        print("   → Set: export GMAIL_ADDRESS=your-email@gmail.com")

    if not os.environ.get("GMAIL_APP_PASSWORD"):
        print("   [WARNING] GMAIL_APP_PASSWORD not set")
        print("   → Set: export GMAIL_APP_PASSWORD=your-app-password")

    try:
        import socks
    except ImportError:
        print("   [WARNING] PySocks not installed")
        print("   → Install: pip install pysocks")

    print()
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_hermes_environment()
