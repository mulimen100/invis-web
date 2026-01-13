import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import json
import os

class AlertSystem:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = logging.getLogger("TitanAlerts")
        
    def _load_config(self):
        if not os.path.exists(self.config_path):
            return {}
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def send_email(self, subject, message_body):
        notifications = self.config.get('notifications', {})
        if not notifications.get('enabled', False):
            self.logger.info("Alerts disabled in config.")
            return

        sender_email = notifications.get('email_sender')
        receiver_email = notifications.get('email_receiver')
        password = notifications.get('email_password')

        if not sender_email or not receiver_email or not password:
            self.logger.warning("Missing email credentials in config.")
            return

        message = MIMEMultipart("alternative")
        message["Subject"] = f"[TITAN] {subject}"
        message["From"] = sender_email
        message["To"] = receiver_email

        # Plain text version
        text = f"""\
Titan Hammer Alert
------------------
{message_body}

Time: {self._get_time()}
"""
        # HTML version
        html = f"""\
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #2563eb;">Titan Hammer Alert</h2>
    <hr style="border: 1px solid #eee;">
    <p style="font-size: 16px; white-space: pre-wrap;">{message_body}</p>
    <br>
    <p style="font-size: 12px; color: #999;">Generated at {self._get_time()}</p>
  </body>
</html>
"""

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            self.logger.info(f"Email sent to {receiver_email}: {subject}")
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")

    def _get_time(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
