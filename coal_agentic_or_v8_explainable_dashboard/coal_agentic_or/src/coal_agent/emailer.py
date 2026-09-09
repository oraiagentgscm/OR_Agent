from __future__ import annotations
import mimetypes
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from typing import Iterable


class EmailConfigError(RuntimeError):
    pass


def email_enabled() -> bool:
    return os.getenv("EMAIL_ENABLED", "false").lower() == "true"


def _recipients():
    raw = os.getenv("EMAIL_TO", "")
    return [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]


def validate_email_config():
    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_TO"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EmailConfigError("Missing email settings: " + ", ".join(missing))


def send_email(subject: str, body: str, attachments: Iterable[Path | str] = ()):
    if not email_enabled():
        return {"sent": False, "reason": "EMAIL_ENABLED=false"}

    validate_email_config()
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    sender = os.environ["EMAIL_FROM"]
    sender_name = os.getenv("EMAIL_FROM_NAME", "Agentic OR Monitor")
    recipients = _recipients()
    use_ssl = os.getenv("SMTP_USE_SSL", "true").lower() == "true"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((sender_name, sender))
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    for attachment in attachments:
        p = Path(attachment)
        if not p.exists() or not p.is_file():
            continue
        ctype, _ = mimetypes.guess_type(str(p))
        if ctype:
            maintype, subtype = ctype.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)

    try:
        if use_ssl or port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=30) as server:
                server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(username, password)
                server.send_message(msg)
        return {"sent": True, "recipients": recipients}
    except Exception as exc:
        return {"sent": False, "reason": f"{type(exc).__name__}: {exc}", "recipients": recipients}
