"""
Notification module for the MAGPIE platform.

This module provides functionality for sending notifications through various channels.
"""

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Any, Union, Callable

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.monitoring.error_tracking import ErrorEvent, error_tracker


class EmailConfig(BaseModel):
    """
    Configuration for email notifications.
    
    Attributes:
        enabled: Whether email notifications are enabled
        smtp_server: SMTP server address
        smtp_port: SMTP server port
        smtp_username: SMTP username
        smtp_password: SMTP password
        use_tls: Whether to use TLS
        from_email: Sender email address
        to_emails: Recipient email addresses
        subject_prefix: Prefix for email subjects
    """
    
    enabled: bool = False
    smtp_server: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = True
    from_email: str = "alerts@example.com"
    to_emails: List[str] = Field(default_factory=list)
    subject_prefix: str = "[MAGPIE ALERT]"


class WebhookConfig(BaseModel):
    """
    Configuration for webhook notifications.
    
    Attributes:
        enabled: Whether webhook notifications are enabled
        url: Webhook URL
        method: HTTP method to use
        headers: HTTP headers to include
        include_traceback: Whether to include traceback in the payload
    """
    
    enabled: bool = False
    url: str = "https://example.com/webhook"
    method: str = "POST"
    headers: Dict[str, str] = Field(default_factory=dict)
    include_traceback: bool = False


class NotificationService:
    """
    Service for sending notifications.
    
    This class provides methods for sending notifications through various channels.
    """
    
    def __init__(
        self,
        email_config: Optional[EmailConfig] = None,
        webhook_config: Optional[WebhookConfig] = None,
    ):
        """
        Initialize the notification service.
        
        Args:
            email_config: Configuration for email notifications
            webhook_config: Configuration for webhook notifications
        """
        self.logger = logger.bind(name=__name__)
        self.email_config = email_config or EmailConfig()
        self.webhook_config = webhook_config or WebhookConfig()
        
        # Register notification handlers
        if self.email_config.enabled:
            error_tracker.register_notification_handler("email", self.send_email_notification)
        
        if self.webhook_config.enabled:
            error_tracker.register_notification_handler("webhook", self.send_webhook_notification)
    
    def send_email_notification(self, error: ErrorEvent) -> bool:
        """
        Send an email notification for an error.
        
        Args:
            error: Error event
            
        Returns:
            bool: True if the notification was sent, False otherwise
        """
        if not self.email_config.enabled:
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email_config.from_email
            msg["To"] = ", ".join(self.email_config.to_emails)
            msg["Subject"] = f"{self.email_config.subject_prefix} {error.severity.upper()}: {error.exception_type} in {error.component}"
            
            # Create message body
            body = f"""
            <html>
            <body>
                <h2>{error.severity.upper()} Error in {error.component}</h2>
                <p><strong>Error:</strong> {error.exception_type}: {error.message}</p>
                <p><strong>Category:</strong> {error.category}</p>
                <p><strong>Component:</strong> {error.component}</p>
                <p><strong>Time:</strong> {error.timestamp}</p>
                <p><strong>Count:</strong> {error.count}</p>
                <p><strong>First Seen:</strong> {error.first_seen}</p>
                <p><strong>Last Seen:</strong> {error.last_seen}</p>
            """
            
            if error.user_id:
                body += f"<p><strong>User ID:</strong> {error.user_id}</p>"
            
            if error.request_id:
                body += f"<p><strong>Request ID:</strong> {error.request_id}</p>"
            
            if error.context:
                body += "<h3>Context</h3><ul>"
                for key, value in error.context.items():
                    body += f"<li><strong>{key}:</strong> {value}</li>"
                body += "</ul>"
            
            if error.traceback:
                body += f"""
                <h3>Traceback</h3>
                <pre>{error.traceback}</pre>
                """
            
            body += """
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, "html"))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
            
            if self.email_config.use_tls:
                server.starttls()
            
            # Login if credentials are provided
            if self.email_config.smtp_username and self.email_config.smtp_password:
                server.login(self.email_config.smtp_username, self.email_config.smtp_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Sent email notification for error: {error.id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def send_webhook_notification(self, error: ErrorEvent) -> bool:
        """
        Send a webhook notification for an error.
        
        Args:
            error: Error event
            
        Returns:
            bool: True if the notification was sent, False otherwise
        """
        if not self.webhook_config.enabled:
            return False
        
        try:
            # Create payload
            payload = {
                "id": error.id,
                "message": error.message,
                "exception_type": error.exception_type,
                "severity": error.severity,
                "category": error.category,
                "component": error.component,
                "timestamp": error.timestamp.isoformat(),
                "count": error.count,
                "first_seen": error.first_seen.isoformat(),
                "last_seen": error.last_seen.isoformat(),
            }
            
            if error.user_id:
                payload["user_id"] = error.user_id
            
            if error.request_id:
                payload["request_id"] = error.request_id
            
            if error.context:
                payload["context"] = error.context
            
            if self.webhook_config.include_traceback and error.traceback:
                payload["traceback"] = error.traceback
            
            # Send webhook request
            with httpx.Client() as client:
                response = client.request(
                    method=self.webhook_config.method,
                    url=self.webhook_config.url,
                    headers=self.webhook_config.headers,
                    json=payload,
                    timeout=10.0,
                )
                
                response.raise_for_status()
            
            self.logger.info(f"Sent webhook notification for error: {error.id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False


# Create notification service based on settings
notification_service = NotificationService(
    email_config=EmailConfig(
        enabled=settings.EMAIL_NOTIFICATIONS_ENABLED,
        smtp_server=settings.EMAIL_SMTP_SERVER,
        smtp_port=settings.EMAIL_SMTP_PORT,
        smtp_username=settings.EMAIL_SMTP_USERNAME,
        smtp_password=settings.EMAIL_SMTP_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        from_email=settings.EMAIL_FROM,
        to_emails=settings.EMAIL_ALERT_RECIPIENTS,
        subject_prefix=settings.EMAIL_SUBJECT_PREFIX,
    ),
    webhook_config=WebhookConfig(
        enabled=settings.WEBHOOK_NOTIFICATIONS_ENABLED,
        url=settings.WEBHOOK_URL,
        method=settings.WEBHOOK_METHOD,
        headers=settings.WEBHOOK_HEADERS,
        include_traceback=settings.WEBHOOK_INCLUDE_TRACEBACK,
    ),
)
