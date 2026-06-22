import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime
import os

logger = logging.getLogger(__name__)


def send_report(
    excel_path: str,
    from_addr: str,
    to_addr: str,
    smtp_host: str,
    smtp_port: int,
    smtp_password: str,
    deal_summary: str = "",
):
    filename = os.path.basename(excel_path)
    today    = datetime.now().strftime("%d %b %Y")

    msg = MIMEMultipart()
    msg["From"]    = from_addr
    msg["To"]      = to_addr
    msg["Subject"] = f"FARE MATRIX — {today} Price Report"

    body = f"""Hi,

Your latest travel price report is attached: {filename}

{deal_summary}

This report was generated automatically by FARE MATRIX.
Sources: Bedsonline (Hotelbeds) · Amadeus Flights
"""
    msg.attach(MIMEText(body, "plain"))

    with open(excel_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(from_addr, smtp_password)
            server.sendmail(from_addr, to_addr, msg.as_string())
        logger.info("Email sent to %s", to_addr)
    except Exception as e:
        logger.error("Email send failed: %s", e)


def send_deal_alert(
    deal_text: str,
    from_addr: str,
    to_addr: str,
    smtp_host: str,
    smtp_port: int,
    smtp_password: str,
):
    msg = MIMEMultipart()
    msg["From"]    = from_addr
    msg["To"]      = to_addr
    msg["Subject"] = "FARE MATRIX — Deal Alert!"

    body = f"""DEAL ALERT

A price has dropped below your threshold:

{deal_text}

Check your latest report for full details.
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(from_addr, smtp_password)
            server.sendmail(from_addr, to_addr, msg.as_string())
        logger.info("Deal alert sent")
    except Exception as e:
        logger.error("Alert email failed: %s", e)
