#!/usr/bin/env python3
import os
import smtplib
from pathlib import Path
from datetime import date
from email.message import EmailMessage

REPORT_MD = Path("data/agents/daily_betting_angles.md")
REPORT_HTML = Path("data/agents/daily_betting_angles.html")
REPORT_CSV = Path("data/agents/daily_betting_angles.csv")

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
if not REPORT_MD.exists() and not REPORT_HTML.exists():
    raise SystemExit("No daily betting angles report found.")

text_body = REPORT_MD.read_text(errors="ignore") if REPORT_MD.exists() else "Daily betting angles report attached."
html_body = REPORT_HTML.read_text(errors="ignore") if REPORT_HTML.exists() else None

msg = EmailMessage()
msg["From"] = sender
msg["To"] = recipient
msg["Subject"] = f"Daily NCAAF Betting Angles — {date.today().isoformat()}"

if html_body:
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
else:
    msg.set_content(text_body)

if REPORT_MD.exists():
    msg.add_attachment(
        REPORT_MD.read_text(errors="ignore").encode("utf-8"),
        maintype="text",
        subtype="markdown",
        filename="daily_betting_angles.md",
    )

if REPORT_CSV.exists():
    msg.add_attachment(
        REPORT_CSV.read_bytes(),
        maintype="text",
        subtype="csv",
        filename="daily_betting_angles.csv",
    )

with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
    smtp.starttls()
    smtp.login(sender, password)
    smtp.send_message(msg)

print(f"Sent daily betting angles email to {recipient}")
