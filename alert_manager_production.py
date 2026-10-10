#!/usr/bin/env python3
"""
Alert Manager for Market-Pie5-Bot
Sends email and SMS alerts for critical events
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertManager:
    """Manages alerts for trading bot critical events"""
    
    def __init__(self):
        """Initialize alert manager with environment configuration"""
        self.enabled = os.getenv('ALERTS_ENABLED', 'false').lower() == 'true'
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.example.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.alert_email = os.getenv('ALERT_EMAIL', '')
        
        # SMS configuration (via email gateway)
        self.sms_gateway = os.getenv('SMS_GATEWAY', '')  # e.g., operator@example.com
        
        # Alert thresholds
        self.max_daily_loss_pct = float(os.getenv('ALERT_MAX_DAILY_LOSS_PCT', '5.0'))
        self.min_capital_pct = float(os.getenv('ALERT_MIN_CAPITAL_PCT', '10.0'))
        
        if self.enabled:
            logger.info("AlertManager initialized - alerts enabled")
            if not self.smtp_user or not self.alert_email:
                logger.warning("Alert system enabled but SMTP/email not configured")
        else:
            logger.info("AlertManager initialized - alerts disabled")
    
    def send_alert(
        self,
        level: AlertLevel,
        subject: str,
        message: str,
        send_sms: bool = False
    ) -> bool:
        """
        Send alert via email and optionally SMS
        
        Args:
            level: Alert severity level
            subject: Alert subject line
            message: Alert message body
            send_sms: Whether to also send SMS (critical alerts)
        
        Returns:
            True if alert sent successfully
        """
        if not self.enabled:
            logger.debug(f"Alert not sent (disabled): {subject}")
            return False
        
        if not self.smtp_user or not self.alert_email:
            logger.error("Cannot send alert - SMTP configuration incomplete")
            return False
        
        try:
            # Prepare email
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            full_subject = f"[{level.value}] Market-Bot: {subject}"
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.alert_email
            msg['Subject'] = full_subject
            
            body = f"""
Market-Pie5-Bot Alert
Time: {timestamp}
Level: {level.value}

{message}

---
This is an automated alert from your trading bot.
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert sent successfully: {subject}")
            
            # Send SMS for critical alerts
            if send_sms and self.sms_gateway and level == AlertLevel.CRITICAL:
                self._send_sms(subject, message)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    def _send_sms(self, subject: str, message: str) -> bool:
        """Send SMS via email gateway"""
        try:
            # SMS messages should be brief
            sms_text = f"{subject}: {message[:100]}"
            
            msg = MIMEText(sms_text)
            msg['From'] = self.smtp_user
            msg['To'] = self.sms_gateway
            msg['Subject'] = ''
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info("SMS alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def alert_bot_stopped(self, reason: str = "Unknown"):
        """Alert when bot stops unexpectedly"""
        self.send_alert(
            AlertLevel.CRITICAL,
            "Bot Stopped",
            f"Trading bot has stopped.\nReason: {reason}",
            send_sms=True
        )
    
    def alert_excessive_loss(self, loss_pct: float, current_capital: float):
        """Alert when daily loss exceeds threshold"""
        if loss_pct >= self.max_daily_loss_pct:
            self.send_alert(
                AlertLevel.CRITICAL,
                "Excessive Daily Loss",
                f"Daily loss: {loss_pct:.2f}%\n"
                f"Current capital: ${current_capital:,.2f}\n"
                f"Threshold: {self.max_daily_loss_pct}%",
                send_sms=True
            )
    
    def alert_capital_floor_breach(self, current_capital: float, floor: float):
        """Alert when capital falls below floor"""
        self.send_alert(
            AlertLevel.CRITICAL,
            "Capital Floor Breach",
            f"Current capital: ${current_capital:,.2f}\n"
            f"Capital floor: ${floor:,.2f}\n"
            f"Bot trading paused for safety",
            send_sms=True
        )
    
    def alert_api_failure(self, api_name: str, error: str):
        """Alert on critical API failures"""
        self.send_alert(
            AlertLevel.ERROR,
            f"{api_name} API Failure",
            f"API: {api_name}\nError: {error}\n"
            f"Bot may be operating with degraded functionality"
        )
    
    def alert_trade_executed(self, symbol: str, action: str, quantity: float, price: float):
        """Info alert for trade execution (optional)"""
        if os.getenv('ALERT_ON_TRADES', 'false').lower() == 'true':
            self.send_alert(
                AlertLevel.INFO,
                f"Trade: {action} {symbol}",
                f"Executed {action} on {symbol}\n"
                f"Quantity: {quantity}\nPrice: ${price:.2f}"
            )
    
    def alert_pdt_warning(self, day_trades_used: int):
        """Alert when approaching PDT limit"""
        if day_trades_used >= 2:  # Warn at 2 of 3 allowed
            self.send_alert(
                AlertLevel.WARNING,
                "PDT Limit Warning",
                f"Day trades used: {day_trades_used}/3\n"
                f"Approaching Pattern Day Trading limit"
            )
    
    def alert_emergency_stop(self, reason: str):
        """Alert when emergency stop is triggered"""
        self.send_alert(
            AlertLevel.CRITICAL,
            "EMERGENCY STOP ACTIVATED",
            f"Emergency stop has been triggered.\nReason: {reason}\n"
            f"All trading activity halted.",
            send_sms=True
        )


# Global instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global AlertManager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


if __name__ == "__main__":
    # Test alert system
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Set test environment
    os.environ['ALERTS_ENABLED'] = 'true'
    
    manager = get_alert_manager()
    
    if not manager.smtp_user:
        print("Error: Set SMTP_USER and SMTP_PASSWORD to test alerts")
        sys.exit(1)
    
    print("Testing alert system...")
    success = manager.send_alert(
        AlertLevel.INFO,
        "Test Alert",
        "This is a test alert from the trading bot.\nIf you receive this, the alert system is working correctly."
    )
    
    if success:
        print("✓ Test alert sent successfully")
    else:
        print("✗ Failed to send test alert")
