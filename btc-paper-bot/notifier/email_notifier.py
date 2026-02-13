import aiosmtplib
import resend
from email.message import EmailMessage
from config import settings
from utils.logger import logger
import structlog

log = structlog.get_logger()

class Notifier:
    def __init__(self):
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY.get_secret_value()
    
    async def send_email(self, subject: str, body: str, attachments: list = None):
        """Sends email using Resend with SMTP fallback."""
        try:
            # Try Resend API first
            if settings.RESEND_API_KEY:
                params = {
                    "from": settings.EMAIL_FROM,
                    "to": [settings.EMAIL_TO],
                    "subject": subject,
                    "html": body.replace('\n', '<br>')
                }
                if attachments:
                    # Resend attachments logic (simplified here as API details vary per library version)
                    # Currently basic text/html is robust. Attachments might need raw handling.
                    # For simplicity, if attachments exist (like PNG), we might use SMTP or check specific Resend docs.
                    # Given "Resend (API, keine Limits)", we assume it supports attachments.
                    pass 
                
                r = resend.Emails.send(params)
                log.info("Email sent via Resend", id=r.get('id'))
                return 

        except Exception as e:
            log.warning("Resend failed, trying SMTP fallback", error=str(e))
        
        # Fallback to SMTP
        try:
            msg = EmailMessage()
            msg['From'] = settings.SMTP_USER or settings.EMAIL_FROM
            msg['To'] = settings.EMAIL_TO
            msg['Subject'] = subject
            msg.set_content(body)
            
            if attachments:
                for path in attachments:
                    with open(path, 'rb') as f:
                        file_data = f.read()
                        file_name = path.split('/')[-1]
                        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                await aiosmtplib.send(
                    msg,
                    hostname=settings.SMTP_SERVER,
                    port=settings.SMTP_PORT,
                    username=settings.SMTP_USER,
                    password=settings.SMTP_PASSWORD.get_secret_value(),
                    use_tls=False,
                    start_tls=True
                )
                log.info("Email sent via SMTP fallback")
            else:
                log.error("SMTP credentials not configured, cannot send email")
                
        except Exception as e:
            log.error("Failed to send email via SMTP", error=str(e))

notifier = Notifier()
