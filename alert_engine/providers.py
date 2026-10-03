"""
alert_engine/providers.py
Notification providers for Phylax: Console/Mock, Twilio (SMS/WhatsApp), SMTP (Email).
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any


class BaseNotificationProvider:
    channel_name: str = "base"

    def send(self, recipient: str, title: str, message: str, metadata: Dict[str, Any]) -> bool:
        raise NotImplementedError()


class MockConsoleProvider(BaseNotificationProvider):
    channel_name: str = "console_mock"

    def send(self, recipient: str, title: str, message: str, metadata: Dict[str, Any]) -> bool:
        print("\n==================================================================")
        print(f"[PHYLAX DISPATCHER - {self.channel_name.upper()}]")
        print(f"TO: {recipient}")
        print(f"SUBJECT: {title}")
        print(f"BODY:\n{message}")
        if metadata.get("ack_url"):
            print(f"ACK LINK: {metadata['ack_url']}")
        print("==================================================================\n")
        return True


class TwilioSMSProvider(BaseNotificationProvider):
    channel_name: str = "SMS"

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "")

    def send(self, recipient: str, title: str, message: str, metadata: Dict[str, Any]) -> bool:
        if not self.account_sid or not self.auth_token or self.account_sid.startswith("YOUR_"):
            # Fall back to console provider if credentials missing
            return MockConsoleProvider().send(recipient, title, message, metadata)

        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            body = f"{title}\n{message}\nAck: {metadata.get('ack_url', '')}"
            client.messages.create(body=body, from_=self.from_number, to=recipient)
            return True
        except Exception as e:
            print(f"[TWILIO ERROR] {e}")
            return MockConsoleProvider().send(recipient, title, message, metadata)


class EmailSMTPProvider(BaseNotificationProvider):
    channel_name: str = "Email"

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USERNAME", "")
        self.smtp_pass = os.getenv("SMTP_PASSWORD", "")

    def send(self, recipient: str, title: str, message: str, metadata: Dict[str, Any]) -> bool:
        if not self.smtp_user or "your_email" in self.smtp_user:
            return MockConsoleProvider().send(recipient, title, message, metadata)

        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = recipient
            msg["Subject"] = title

            html_content = f"""
            <div style="font-family: Arial, sans-serif; background-color: #0b0e14; color: #e2e8f0; padding: 20px; border-radius: 8px;">
                <h2 style="color: #ef4444; border-bottom: 2px solid #ef4444; padding-bottom: 8px;">🚨 {title}</h2>
                <p style="font-size: 16px; line-height: 1.5;">{message}</p>
                <div style="margin-top: 24px;">
                    <a href="{metadata.get('ack_url', '#')}" style="background-color: #06b6d4; color: #000; font-weight: bold; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        ACKNOWLEDGE INCIDENT & STOP ESCALATION
                    </a>
                </div>
            </div>
            """
            msg.attach(MIMEText(html_content, "html"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, [recipient], msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"[SMTP ERROR] {e}")
            return MockConsoleProvider().send(recipient, title, message, metadata)
