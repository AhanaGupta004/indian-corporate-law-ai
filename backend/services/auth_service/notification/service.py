import logging
from typing import Protocol
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
import os

logger = logging.getLogger(__name__)

class NotificationProvider(Protocol):
    async def send_agent_credentials(self, email: EmailStr, password: str) -> None:
        ...
        
    async def send_otp(self, email: EmailStr, otp: str) -> None:
        ...


class EmailNotificationProvider:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME = os.getenv("MAIL_USERNAME", "dummy@gmail.com"),
            MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "dummy_app_password"),
            MAIL_FROM = os.getenv("MAIL_FROM", "noreply@legalbuddy.com"),
            MAIL_PORT = 587,
            MAIL_SERVER = "smtp.gmail.com",
            MAIL_STARTTLS = True,
            MAIL_SSL_TLS = False,
            USE_CREDENTIALS = True,
            VALIDATE_CERTS = True
        )
        self.fm = FastMail(self.conf)

    async def send_agent_credentials(self, email: EmailStr, password: str) -> None:
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0; padding:0; background-color:#f9fafb; font-family:'Inter', 'Poppins', Arial, sans-serif; color:#1f2937;">
            <div style="max-width:600px; margin:40px auto; background-color:#ffffff; border-radius:16px; overflow:hidden; border:1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <div style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); padding:40px 30px; text-align:center;">
                    <h1 style="color:#ffffff; font-size:28px; margin:0; font-weight:800; letter-spacing:-0.5px;">LegalBuddy</h1>
                </div>
                <div style="padding:40px 30px;">
                    <h2 style="color:#111827; font-size:22px; margin-top:0; font-weight:700;">Welcome to the Platform</h2>
                    <p style="color:#4b5563; font-size:16px; line-height:1.6;">Your account has been <strong>approved</strong>. You now have full access to our AI legal intelligence platform.</p>
                    
                    <div style="background-color:#fff7ed; border:1px solid #fed7aa; border-left:4px solid #f97316; border-radius:8px; padding:20px; margin:30px 0;">
                        <p style="margin:0 0 12px 0; color:#ea580c; font-size:13px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;">Your Credentials</p>
                        <p style="margin:0 0 8px 0; font-size:15px; color:#374151;"><strong>Email:</strong> {email}</p>
                        <p style="margin:0; font-size:15px; color:#374151;"><strong>Password:</strong> <span style="color:#ea580c; font-family:monospace; font-weight:600; font-size:16px; background:#ffedd5; padding:4px 8px; border-radius:6px; margin-left:4px;">{password}</span></p>
                    </div>
                    
                    <p style="color:#6b7280; font-size:14px; line-height:1.5;">For security reasons, we highly recommend changing your password immediately after logging in.</p>
                </div>
                <div style="background-color:#f3f4f6; padding:20px; text-align:center; border-top:1px solid #e5e7eb;">
                    <p style="margin:0; color:#9ca3af; font-size:12px;">© 2026 LegalBuddy. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        message = MessageSchema(
            subject="LegalBuddy - Your Agent Account is Approved",
            recipients=[email],
            body=html,
            subtype=MessageType.html
        )

        try:
            await self.fm.send_message(message)
            logger.info(f"Credentials email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")

    async def send_otp(self, email: EmailStr, otp: str) -> None:
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0; padding:0; background-color:#f9fafb; font-family:'Inter', 'Poppins', Arial, sans-serif; color:#1f2937;">
            <div style="max-width:600px; margin:40px auto; background-color:#ffffff; border-radius:16px; overflow:hidden; border:1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <div style="padding:40px 30px; text-align:center;">
                    <h1 style="color:#ea580c; font-size:24px; margin:0 0 20px 0; font-weight:800; letter-spacing:-0.5px;">LegalBuddy</h1>
                    <h2 style="color:#111827; font-size:22px; margin-top:0; font-weight:700;">Login Verification</h2>
                    <p style="color:#4b5563; font-size:16px; line-height:1.6; margin-bottom:30px;">Please use the following 6-digit code to complete your secure login process. This code will expire in <strong>5 minutes</strong>.</p>
                    
                    <div style="background-color:#fff7ed; border:1px dashed #f97316; border-radius:12px; padding:25px; margin:0 auto; display:inline-block;">
                        <div style="font-size:42px; font-weight:900; letter-spacing:10px; color:#ea580c; font-family:monospace; margin-left:10px;">{otp}</div>
                    </div>
                    
                    <p style="color:#9ca3af; font-size:13px; margin-top:40px; line-height:1.5;">If you did not attempt to log in, please ignore this email or contact support immediately.</p>
                </div>
            </div>
        </body>
        </html>
        """

        message = MessageSchema(
            subject="LegalBuddy - Your Secure Login Code",
            recipients=[email],
            body=html,
            subtype=MessageType.html
        )

        try:
            await self.fm.send_message(message)
            logger.info(f"OTP email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send OTP to {email}: {e}")
            raise ValueError("Failed to send OTP email")


def get_notification_provider() -> NotificationProvider:
    return EmailNotificationProvider()
