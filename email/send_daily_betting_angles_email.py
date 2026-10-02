#!/usr/bin/env python3
import os
import smtplib
import fcntl
import hashlib
import json
from pathlib import Path
from datetime import date, datetime, timezone
from email.message import EmailMessage
from email.utils import make_msgid

REPORT_MD = Path("data/agents/daily_betting_angles.md")
REPORT_HTML = Path("data/agents/daily_betting_angles.html")
REPORT_CSV = Path("data/agents/daily_betting_angles.csv")
SEND_LEDGER = Path("data/control/daily_email_send_ledger.json")
SEND_LOCK = Path("data/control/daily_email_send_ledger.lock")

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

send_date = date.today().isoformat()
subject = f"Daily NCAAF Betting Angles — {send_date}"
send_key = hashlib.sha256(f"{send_date}\0{recipient}".encode()).hexdigest()
message_id = make_msgid(idstring=f"ncaaf-daily-{send_date}")


def read_ledger() -> dict:
    if not SEND_LEDGER.exists():
        return {"schema_version": 1, "sends": {}}
    payload = json.loads(SEND_LEDGER.read_text())
    if not isinstance(payload, dict) or not isinstance(payload.get("sends"), dict):
        raise SystemExit(f"Invalid email send ledger: {SEND_LEDGER}")
    return payload


def write_ledger(payload: dict) -> None:
    SEND_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    temporary = SEND_LEDGER.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(SEND_LEDGER)


SEND_LOCK.parent.mkdir(parents=True, exist_ok=True)
lock_handle = SEND_LOCK.open("a+")
fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
ledger = read_ledger()
prior = ledger["sends"].get(send_key)
if prior and prior.get("status") in {"IN_FLIGHT", "SENT", "UNKNOWN"}:
    print(
        "Daily email not sent: duplicate-protection claim exists "
        f"({prior.get('status')}) for {send_date} to {recipient}"
    )
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    lock_handle.close()
    raise SystemExit(0)

claimed_at = datetime.now(timezone.utc).isoformat()
ledger["sends"][send_key] = {
    "date": send_date,
    "recipient": recipient,
    "subject": subject,
    "message_id": message_id,
    "status": "IN_FLIGHT",
    "claimed_at_utc": claimed_at,
}
write_ledger(ledger)
fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
lock_handle.close()

text_body = REPORT_MD.read_text(errors="ignore") if REPORT_MD.exists() else "Daily betting angles report attached."
html_body = REPORT_HTML.read_text(errors="ignore") if REPORT_HTML.exists() else None

msg = EmailMessage()
msg["From"] = sender
msg["To"] = recipient
msg["Subject"] = subject
msg["Message-ID"] = message_id

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

try:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(msg)
except BaseException as exc:
    ledger = read_ledger()
    ledger["sends"][send_key].update(
        {
            "status": "UNKNOWN",
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": type(exc).__name__,
        }
    )
    write_ledger(ledger)
    raise

ledger = read_ledger()
ledger["sends"][send_key].update(
    {
        "status": "SENT",
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
)
write_ledger(ledger)

print(f"Sent daily betting angles email to {recipient}; Message-ID: {message_id}")
