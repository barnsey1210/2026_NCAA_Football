#!/usr/bin/env python3
import os
import smtplib
from pathlib import Path
from datetime import date
from email.message import EmailMessage

REPORT = Path("data/agents/daily_betting_angles.md")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

sender = os.environ.get("NCAAF_GMAIL_USER")
password = os.environ.get("NCAAF_GMAIL_APP_PASSWORD")
recipient = os.environ.get("NCAAF_EMAIL_TO")

if not sender:
    raise SystemExit("Missing NCAAF_GMAIL_USER environment variable.")
if not password:
    raise SystemExit("Missing NCAAF_GMAIL_APP_PASSWORD environment variable.")
if not recipient:
    raise SystemExit("Missing NCAAF_EMAIL_TO environment variable.")
if not REPORT.exists():
    raise SystemExit(f"Report not found: {REPORT}")

body = REPORT.read_text(errors="ignore")

msg = EmailMessage()
msg["From"] = sender
msg["To"] = recipient
msg["Subject"] = f"Daily NCAAF Betting Angles — {date.today().isoformat()}"
msg.set_content(body)

# Also attach the markdown report.
msg.add_attachment(
    body.encode("utf-8"),
    maintype="text",
    subtype="markdown",
    filename="daily_betting_angles.md",
)

with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
    smtp.starttls()
    smtp.login(sender, password)
    smtp.send_message(msg)

print(f"Sent daily betting angles email to {recipient}")
