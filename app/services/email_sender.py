"""
Email Sender Service
Handles SMTP authentication and dispatches audit reports with file attachments.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Configure these via environment variables in production for security
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your-scanner-email@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your-gmail-app-password")

def send_audit_email(recipient_email: str, target_url: str, report_filepath: str, markdown_content: str) -> bool:
    """
    Sends the generated markdown audit report via SMTP to the client.
    """
    if not SENDER_EMAIL or SENDER_PASSWORD == "your-gmail-app-password":
        print("[Email Warning] SMTP credentials are not configured. Skipping live email dispatch.")
        return False

    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = f"Your Trilloka Financial Leak Audit Report for {target_url}"

        # Email body text
        body = f"""
Hello,

Your website audit for {target_url} has been successfully completed by the Trilloka Engine.

Attached to this email is your complete Master Report containing your prioritized financial leaks, severity scores, and custom resolution blueprints.

Stay consistent,
The Trilloka Team
        """
        msg.attach(MIMEText(body, 'plain'))

        # Attach the Markdown report file
        if os.path.exists(report_filepath):
            with open(report_filepath, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(report_filepath)}"'
            )
            msg.attach(part)

        # Connect to SMTP server and send
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipient_email, text)
        server.quit()
        
        print(f"-> Email successfully sent to {recipient_email}")
        return True

    except Exception as e:
        print(f"[Email Error] Failed to send email: {str(e)}")
        return False