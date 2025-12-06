"""
Email sending module for password reset and notifications.
Supports multiple email services (SMTP, SendGrid, etc.)
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
from pathlib import Path


class EmailSender:
    """Email sending utility with support for multiple providers."""
    
    def __init__(self):
        """Initialize email sender with configuration from environment variables."""
        self.enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        self.provider = os.getenv('EMAIL_PROVIDER', 'smtp').lower()  # smtp, sendgrid, etc.
        
        # SMTP Configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # Email Configuration
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'SmartCursor')
        
        # SendGrid Configuration (if using SendGrid)
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', '')
        
        # Base URL for reset links
        self.base_url = os.getenv('BASE_URL', 'http://localhost:5050')
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
        
        Returns:
            Dictionary with success status and message
        """
        if not self.enabled:
            return {
                "ok": False,
                "error": "Email sending is disabled. Set EMAIL_ENABLED=true to enable."
            }
        
        if not to_email:
            return {"ok": False, "error": "Recipient email is required"}
        
        try:
            if self.provider == 'smtp':
                return self._send_via_smtp(to_email, subject, html_body, text_body)
            elif self.provider == 'sendgrid':
                return self._send_via_sendgrid(to_email, subject, html_body, text_body)
            else:
                return {"ok": False, "error": f"Unsupported email provider: {self.provider}"}
        except Exception as e:
            return {"ok": False, "error": f"Failed to send email: {str(e)}"}
    
    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict:
        """Send email via SMTP."""
        if not self.smtp_user or not self.smtp_password:
            return {
                "ok": False,
                "error": "SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD."
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add plain text part if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"[email] Password reset email sent to {to_email}")
            return {"ok": True, "message": "Email sent successfully"}
        
        except smtplib.SMTPAuthenticationError:
            return {"ok": False, "error": "SMTP authentication failed. Check your credentials."}
        except smtplib.SMTPException as e:
            return {"ok": False, "error": f"SMTP error: {str(e)}"}
        except Exception as e:
            return {"ok": False, "error": f"Failed to send email: {str(e)}"}
    
    def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict:
        """Send email via SendGrid API."""
        if not self.sendgrid_api_key:
            return {
                "ok": False,
                "error": "SendGrid API key not configured. Set SENDGRID_API_KEY."
            }
        
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            from_email = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email)
            
            # Use HTML content if available, otherwise text
            if html_body:
                content = Content("text/html", html_body)
            elif text_body:
                content = Content("text/plain", text_body)
            else:
                return {"ok": False, "error": "Email body is required"}
            
            message = Mail(from_email, to_email_obj, subject, content)
            response = sg.send(message)
            
            if response.status_code in [200, 202]:
                print(f"[email] Password reset email sent to {to_email} via SendGrid")
                return {"ok": True, "message": "Email sent successfully"}
            else:
                return {"ok": False, "error": f"SendGrid error: {response.status_code}"}
        
        except ImportError:
            return {
                "ok": False,
                "error": "SendGrid library not installed. Run: pip install sendgrid"
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to send email via SendGrid: {str(e)}"}
    
    def send_password_reset_email(self, to_email: str, reset_token: str, username: str = None) -> Dict:
        """
        Send password reset email with reset link.
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            username: Username (optional, for personalization)
        
        Returns:
            Dictionary with success status
        """
        reset_url = f"{self.base_url}/reset-password?token={reset_token}"
        
        subject = "Reset Your Password - SmartCursor"
        
        # HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f7fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .button:hover {{ opacity: 0.9; }}
                .footer {{ text-align: center; margin-top: 20px; color: #718096; font-size: 12px; }}
                .token {{ background: #e2e8f0; padding: 10px; border-radius: 4px; font-family: monospace; 
                         word-break: break-all; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Reset Your Password</h1>
                </div>
                <div class="content">
                    <p>Hello{' ' + username if username else ''},</p>
                    <p>You requested to reset your password for your SmartCursor account. Click the button below to reset your password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <div class="token">{reset_url}</div>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you didn't request a password reset, please ignore this email. Your password will not be changed.</p>
                    <p>Best regards,<br>The SmartCursor Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
        Reset Your Password - SmartCursor
        
        Hello{' ' + username if username else ''},
        
        You requested to reset your password for your SmartCursor account.
        
        Click this link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email. Your password will not be changed.
        
        Best regards,
        The SmartCursor Team
        
        ---
        This is an automated message, please do not reply.
        """
        
        return self.send_email(to_email, subject, html_body, text_body)


# Global email sender instance
_email_sender = None

def get_email_sender() -> EmailSender:
    """Get or create global email sender instance."""
    global _email_sender
    if _email_sender is None:
        _email_sender = EmailSender()
    return _email_sender

