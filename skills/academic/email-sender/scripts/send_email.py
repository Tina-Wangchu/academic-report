#!/usr/bin/env python3
"""
Email Sender — Gmail SMTP with retry and logging.

Usage:
    python send_email.py --to recipient@example.com --subject "标题" \
        --body-file /tmp/email_body.html --body-type html \
        [--attach file1.pdf file2.xlsx] \
        [--log /path/to/email_log.json] \
        [--from-name "Sender Name"]

All Gmail credentials are read from environment variables:
    GMAIL_ADDRESS     — your Gmail address (e.g. you@gmail.com)
    GMAIL_APP_PASSWORD — 16-char app-specific password
    SMTP_SOCKS_PROXY  — (optional) SOCKS5 proxy, e.g. socks5://127.0.0.1:7891

Requires Python 3.6+. PySocks (pip install pysocks) required if using SOCKS5 proxy.
"""

import argparse
import json
import os
import smtplib
import socket
import sys
import time
from datetime import datetime, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr

# ==================== Configuration ====================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 15]  # seconds between retries
DEFAULT_LOG_PATH = os.path.expanduser("~/.hermes/email_log.json")
MAX_LOG_ENTRIES = 200

# ==================== SOCKS5 Proxy Support ====================

def _create_socketsrc(proxy_host, proxy_port):
    """Create a socket source function that routes through SOCKS5 proxy."""
    try:
        import socks
    except ImportError:
        print(
            "Error: SOCKS5 proxy requires PySocks. Install with: pip install pysocks",
            file=sys.stderr,
        )
        sys.exit(1)

    def socketsrc(family, *args, **kwargs):
        sock = socks.socksocket(family=family, *args, **kwargs)
        sock.setproxy(socks.PROXY_TYPE_SOCKS5, proxy_host, proxy_port)
        return sock

    return socketsrc


def _get_smtp_connection():
    """Create SMTP connection, optionally through SOCKS5 proxy."""
    proxy_str = os.environ.get("SMTP_SOCKS_PROXY", "")

    if proxy_str:
        try:
            import socks
        except ImportError:
            print(
                "Error: SOCKS5 proxy requires PySocks. Install with: pip install pysocks",
                file=sys.stderr,
            )
            sys.exit(1)

        proxy_str = proxy_str.replace("socks5://", "")
        if ":" in proxy_str:
            proxy_host, proxy_port = proxy_str.rsplit(":", 1)
            proxy_port = int(proxy_port)
        else:
            proxy_host = proxy_str
            proxy_port = 1080

        # Create SOCKS5 socket and connect
        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setproxy(socks.PROXY_TYPE_SOCKS5, proxy_host, proxy_port)
        sock.settimeout(30)
        sock.connect((SMTP_SERVER, SMTP_PORT))

        # Create SMTP without auto-connect, then inject the SOCKS5 socket
        server = smtplib.SMTP()
        server.sock = sock
        server.file = sock.makefile('rwb')
        server._host = SMTP_SERVER  # Required for STARTTLS TLS handshake
        # Read the initial SMTP banner (required before EHLO)
        server.getreply()
        return server
    else:
        return smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)


# ==================== SMTP Sender ====================

def send_email(
    to_list,
    subject,
    body_content,
    body_type="html",
    cc_list=None,
    from_name=None,
    reply_to=None,
    attachments=None,
):
    """
    Send email via Gmail SMTP.

    Returns dict with status, message, and timestamp.
    """
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not gmail_address or not app_password:
        return {
            "status": "error",
            "error": "Missing credentials: set GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Build recipients
    all_recipients = list(to_list)
    if cc_list:
        all_recipients.extend(cc_list)

    # Build MIME message
    msg = MIMEMultipart()
    msg["From"] = formataddr((from_name, gmail_address)) if from_name else gmail_address
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Subject"] = subject
    msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Body
    msg.attach(MIMEText(body_content, body_type, "utf-8"))

    # Attachments
    if attachments:
        for filepath in attachments:
            if not os.path.isfile(filepath):
                return {
                    "status": "error",
                    "error": f"Attachment not found: {filepath}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            filename = os.path.basename(filepath)
            with open(filepath, "rb") as f:
                part = MIMEApplication(f.read(), Name=filename)
                part["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(part)

    # Send with retry
    last_error = None
    for attempt in range(MAX_RETRIES):
        server = None
        try:
            server = _get_smtp_connection()
            server.ehlo_or_helo_if_needed()
            server.starttls()
            server.ehlo_or_helo_if_needed()
            server.login(gmail_address, app_password)
            server.sendmail(gmail_address, all_recipients, msg.as_string())
            server.quit()

            return {
                "status": "success",
                "from": gmail_address,
                "to": to_list,
                "cc": cc_list or [],
                "subject": subject,
                "body_type": body_type,
                "attachments": [os.path.basename(f) for f in (attachments or [])],
                "attempts": attempt + 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except smtplib.SMTPAuthenticationError as e:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
            return {
                "status": "error",
                "error": f"Authentication failed: {e}",
                "hint": "Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD. App password may have been revoked.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except smtplib.SMTPRecipientsRefused as e:
            return {
                "status": "error",
                "error": f"Recipient refused: {e}",
                "hint": "Verify all email addresses are correct.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except (smtplib.SMTPServerDisconnected, ConnectionError, OSError) as e:
            last_error = str(e)
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"  Retry {attempt + 1}/{MAX_RETRIES} in {wait}s... (error: {e})", file=sys.stderr)
                time.sleep(wait)
            else:
                return {
                    "status": "error",
                    "error": f"Failed after {MAX_RETRIES} retries: {last_error}",
                    "hint": "Check network connection to smtp.gmail.com:587. May need proxy/VPN.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

    return {
        "status": "error",
        "error": f"Unknown error after {MAX_RETRIES} retries: {last_error}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ==================== Logging ====================

def append_log(result, log_path=DEFAULT_LOG_PATH):
    """Append send result to JSON log file."""
    entry = {
        **result,
        "_logged_at": datetime.now(timezone.utc).isoformat(),
    }

    # Remove from_name from log entry (internal detail)
    entry.pop("from_name", None)

    # Load existing log or create new
    if os.path.isfile(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                log = json.load(f)
        except (json.JSONDecodeError, OSError):
            log = []
    else:
        log = []
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    log.append(entry)

    # Trim to max entries
    if len(log) > MAX_LOG_ENTRIES:
        log = log[-MAX_LOG_ENTRIES:]

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    return log_path


def read_log(log_path=DEFAULT_LOG_PATH, limit=10):
    """Read recent log entries."""
    if not os.path.isfile(log_path):
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        log = json.load(f)
    return log[-limit:]


# ==================== CLI ====================

def main():
    parser = argparse.ArgumentParser(
        description="Send email via Gmail SMTP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # HTML email
  python send_email.py --to alice@example.com --subject "Report" --body-file body.html --body-type html

  # Plain text with attachments
  python send_email.py --to bob@example.com --subject "Data" --body-file msg.txt --body-type plain --attach data.pdf

  # Multiple recipients
  python send_email.py --to alice@example.com bob@example.com --subject "Update" --body-file body.html --body-type html

  # View recent send log
  python send_email.py --log-show
        """,
    )
    parser.add_argument("--to", nargs="+", help="Recipient email(s)")
    parser.add_argument("--cc", nargs="*", help="CC recipient(s)")
    parser.add_argument("--subject", help="Email subject")
    parser.add_argument("--body-file", help="File containing email body")
    parser.add_argument("--body-type", choices=["plain", "html"], default="html", help="Body format (default: html)")
    parser.add_argument("--attach", nargs="*", help="Attachment file(s)")
    parser.add_argument("--from-name", help="Sender display name")
    parser.add_argument("--reply-to", help="Reply-To address")
    parser.add_argument("--log", default=DEFAULT_LOG_PATH, help="Log file path")
    parser.add_argument("--log-show", action="store_true", help="Show recent send log instead of sending")

    args = parser.parse_args()

    # Log show mode
    if args.log_show:
        entries = read_log(args.log)
        if not entries:
            print("No send log entries found.")
            return 0
        for entry in entries:
            status_icon = "[OK]" if entry["status"] == "success" else "[ERROR]"
            print(f"{status_icon} [{entry['timestamp']}] {entry.get('to', '?')} -> {entry.get('subject', '?')}")
            if entry["status"] == "error":
                print(f"   Error: {entry.get('error', 'unknown')}")
        return 0

    # Read body file
    try:
        with open(args.body_file, "r", encoding="utf-8") as f:
            body_content = f.read()
    except FileNotFoundError:
        print(f"Error: Body file not found: {args.body_file}", file=sys.stderr)
        return 1

    # Send
    print(f"Sending to: {', '.join(args.to)}")
    if args.cc:
        print(f"CC: {', '.join(args.cc)}")
    if args.attach:
        print(f"Attachments: {', '.join(os.path.basename(f) for f in args.attach)}")

    result = send_email(
        to_list=args.to,
        cc_list=args.cc,
        subject=args.subject,
        body_content=body_content,
        body_type=args.body_type,
        from_name=args.from_name,
        reply_to=args.reply_to,
        attachments=args.attach,
    )

    # Log result
    log_path = append_log(result, args.log)

    if result["status"] == "success":
        print(f"[OK] Email sent successfully! (attempts: {result['attempts']})")
        print(f"   Log: {log_path}")
        return 0
    else:
        print(f"[ERROR] Failed to send: {result['error']}", file=sys.stderr)
        if "hint" in result:
            print(f"   Hint: {result['hint']}", file=sys.stderr)
        print(f"   Log: {log_path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
