"""
alert_system.py
Sends accident alerts to police, ambulance, and fire contacts via SMS,
voice call (Twilio), and email. Defaults to DRY_RUN mode (set in config.py)
which logs exactly what WOULD be sent, without contacting Twilio/SMTP.

IMPORTANT: Set config.DRY_RUN = False and fill in real Twilio/SMTP
credentials only once this is deployed against a real, authorized
emergency-response workflow. Never point this at real emergency services
during a hackathon demo -- keep DRY_RUN = True and simulate with your own
phone numbers/emails instead.
"""

import os
import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import config

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None  # twilio package optional if running in DRY_RUN only


LOG_PATH = os.path.join("logs", "alerts.log")


def _log(message):
    os.makedirs("logs", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        logger.error(f"Failed writing to log file {LOG_PATH}: {e}")


class EmergencyAlertSystem:
    def __init__(self):
        self.twilio_client = None
        if not config.DRY_RUN:
            if TwilioClient is None:
                raise RuntimeError(
                    "twilio package not installed. Run: pip install twilio"
                )
            self.twilio_client = TwilioClient(
                config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN
            )

    def _build_message(self, clip_path, details):
        involved = details.get("involved_ids", [])
        score = details.get("total_score", 0)
        return (
            f"ACCIDENT DETECTED at {config.CAMERA_LOCATION} "
            f"(GPS: {config.CAMERA_GPS[0]}, {config.CAMERA_GPS[1]}). "
            f"Confidence score: {score}. Vehicles involved: {involved}. "
            f"Clip: {clip_path or 'recording...'}"
        )

    def _send_sms(self, to_number, message):
        if config.DRY_RUN:
            _log(f"[DRY_RUN][SMS -> {to_number}] {message}")
            return
        try:
            self.twilio_client.messages.create(
                body=message, from_=config.TWILIO_FROM_NUMBER, to=to_number
            )
            _log(f"[SMS SENT -> {to_number}]")
        except Exception as e:
            _log(f"[SMS ERROR -> {to_number}] {e}")

    def _make_call(self, to_number, message):
        if config.DRY_RUN:
            _log(f"[DRY_RUN][CALL -> {to_number}] Would place automated voice call: {message}")
            return
        try:
            twiml = f"<Response><Say>{message}</Say></Response>"
            self.twilio_client.calls.create(
                twiml=twiml, from_=config.TWILIO_FROM_NUMBER, to=to_number
            )
            _log(f"[CALL PLACED -> {to_number}]")
        except Exception as e:
            _log(f"[CALL ERROR -> {to_number}] {e}")

    def _send_email(self, to_email, subject, body, attachment_path=None):
        if config.DRY_RUN:
            attach_note = f" (with attachment {attachment_path})" if attachment_path else ""
            _log(f"[DRY_RUN][EMAIL -> {to_email}] {subject}{attach_note}")
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = config.SMTP_USERNAME
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}",
                )
                msg.attach(part)

            with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
                server.starttls()
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                server.send_message(msg)
            _log(f"[EMAIL SENT -> {to_email}]")
        except Exception as e:
            _log(f"[EMAIL ERROR -> {to_email}] {e}")

    def dispatch(self, clip_path, details):
        """
        Notify police, ambulance, and fire simultaneously.
        clip_path: path to the saved (or in-progress) incident video clip.
        details: the details dict returned by AccidentDetector.analyze()
        """
        message = self._build_message(clip_path, details)
        _log(f"=== DISPATCHING EMERGENCY ALERT === {message}")

        for service, contact in config.EMERGENCY_CONTACTS.items():
            phone = contact.get("phone", "")
            email = contact.get("email", "")
            if phone:
                self._send_sms(phone, f"[{service.upper()}] {message}")
                self._make_call(phone, message)
            if email:
                self._send_email(
                    email,
                    subject=f"URGENT: Vehicle Accident Detected - {service.title()} Dispatch",
                    body=message,
                    attachment_path=clip_path,
                )

        _log("=== ALERT DISPATCH COMPLETE ===")

