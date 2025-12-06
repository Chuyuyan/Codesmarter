"""
SMS sending module for password reset notifications.
Uses Twilio for SMS delivery.
"""
import os
from typing import Optional, Dict
from datetime import datetime


class SMSSender:
    """SMS sending utility using Twilio."""
    
    def __init__(self):
        """Initialize SMS sender with configuration from environment variables."""
        self.enabled = os.getenv('SMS_ENABLED', 'false').lower() == 'true'
        
        # Twilio Configuration
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER', '')
        self.messaging_service_sid = os.getenv('TWILIO_MESSAGING_SERVICE_SID', '')
        
        # Base URL for reset links
        self.base_url = os.getenv('BASE_URL', 'http://localhost:5050')
        
        # Initialize Twilio client if credentials are available
        self.client = None
        if self.enabled and self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
            except ImportError:
                print("[sms] Twilio library not installed. Run: pip install twilio")
    
    def send_sms(self, to_number: str, message: str) -> Dict:
        """
        Send an SMS message.
        
        Args:
            to_number: Recipient phone number (E.164 format, e.g., +1234567890)
            message: SMS message text
        
        Returns:
            Dictionary with success status and message
        """
        if not self.enabled:
            return {
                "ok": False,
                "error": "SMS sending is disabled. Set SMS_ENABLED=true to enable."
            }
        
        if not to_number:
            return {"ok": False, "error": "Recipient phone number is required"}
        
        if not message:
            return {"ok": False, "error": "Message is required"}
        
        if not self.client:
            if not self.account_sid or not self.auth_token:
                return {
                    "ok": False,
                    "error": "Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
                }
            return {
                "ok": False,
                "error": "Twilio client not initialized. Install twilio: pip install twilio"
            }
        
        try:
            # Prepare message parameters
            kwargs = {
                "to": to_number,
                "body": message
            }
            
            # Use messaging service SID if available, otherwise use from number
            if self.messaging_service_sid:
                kwargs["messaging_service_sid"] = self.messaging_service_sid
            elif self.from_number:
                kwargs["from_"] = self.from_number
            else:
                return {
                    "ok": False,
                    "error": "Please set TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID in .env"
                }
            
            # Send SMS
            msg = self.client.messages.create(**kwargs)
            
            print(f"[sms] SMS sent successfully to {to_number}. SID: {msg.sid}")
            return {
                "ok": True,
                "message": "SMS sent successfully",
                "sid": msg.sid
            }
        
        except Exception as e:
            error_msg = str(e)
            print(f"[sms] Failed to send SMS: {error_msg}")
            return {
                "ok": False,
                "error": f"Failed to send SMS: {error_msg}"
            }
    
    def send_password_reset_sms(
        self,
        to_number: str,
        reset_token: str,
        username: Optional[str] = None
    ) -> Dict:
        """
        Send password reset SMS with reset link.
        
        Args:
            to_number: Recipient phone number (E.164 format)
            reset_token: Password reset token
            username: Username (optional, for personalization)
        
        Returns:
            Dictionary with success status
        """
        reset_url = f"{self.base_url}/reset-password?token={reset_token}"
        
        # Create SMS message
        message = f"SmartCursor Password Reset\n\n"
        
        if username:
            message += f"Hello {username},\n\n"
        else:
            message += f"Hello,\n\n"
        
        message += f"You requested to reset your password. "
        message += f"Click this link to reset:\n{reset_url}\n\n"
        message += f"This link expires in 1 hour.\n\n"
        message += f"If you didn't request this, please ignore this message."
        
        return self.send_sms(to_number, message)


# Global SMS sender instance
_sms_sender = None

def get_sms_sender() -> SMSSender:
    """Get or create global SMS sender instance."""
    global _sms_sender
    if _sms_sender is None:
        _sms_sender = SMSSender()
    return _sms_sender

