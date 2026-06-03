"""SMTP email service — best-effort."""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import get_settings

log = logging.getLogger(__name__)


def send_email(to: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
    s = get_settings()
    if not s.smtp_host:
        log.info("SMTP not configured; skipping email to %s", to)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = s.smtp_from
    msg["To"] = to
    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as server:
            server.ehlo()
            try:
                server.starttls()
                server.ehlo()
            except Exception:
                pass
            if s.smtp_user:
                server.login(s.smtp_user, s.smtp_password)
            server.sendmail(s.smtp_from, [to], msg.as_string())
        return True
    except Exception as exc:
        log.warning("email send failed: %s", exc)
        return False
