#!/usr/bin/env python3
"""
Simple SMTP email sender using .env configuration.
"""

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


class EmailClient:
    def __init__(self):
        load_dotenv()
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_pass = os.getenv('SMTP_PASS')
        self.email_from = os.getenv('EMAIL_FROM', self.smtp_user)
        self.email_to_default = os.getenv('EMAIL_TO')

    def send_email(self, subject: str, body: str, to: Optional[str] = None, attachments: Optional[List[str]] = None) -> None:
        to_addr = to or self.email_to_default
        if not to_addr:
            raise ValueError("No recipient email set. Provide 'to' or set EMAIL_TO in .env")

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.email_from
        msg['To'] = to_addr
        msg.set_content(body)

        for path_str in attachments or []:
            path = Path(path_str)
            if not path.exists():
                continue
            content = path.read_bytes()
            msg.add_attachment(content, maintype='application', subtype='octet-stream', filename=path.name)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            if self.smtp_user and self.smtp_pass:
                server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)



