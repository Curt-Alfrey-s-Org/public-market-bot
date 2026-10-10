"""
Alert Manager for Market Bot
Popup notifications for high-impact news events and sizzle stocks.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import platform

logger = logging.getLogger(__name__)

# Try different notification libraries based on platform
NOTIFICATION_AVAILABLE = False
notify_func = None

# Try Windows toast notifications first
try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    NOTIFICATION_AVAILABLE = True
    notify_func = 'win10toast'
    logger.info("Alert system initialized (win10toast)")
except ImportError:
    pass

# Fallback to plyer (cross-platform)
if not NOTIFICATION_AVAILABLE:
    try:
        from plyer import notification
        NOTIFICATION_AVAILABLE = True
        notify_func = 'plyer'
        logger.info("Alert system initialized (plyer)")
    except ImportError:
        logger.warning("No notification library available - alerts disabled")


class AlertManager:
    """
    Manage desktop notifications for:
    1. High-impact news events (IPO, M&A, Regulatory)
    2. Sizzle stocks (unusual volume, big price moves)
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize alert manager.
        
        Args:
            enabled: Whether alerts are enabled
        """
        self.enabled = enabled and NOTIFICATION_AVAILABLE
        self.alert_history: List[Dict] = []  # Track recent alerts
        self.max_history = 100
        
        if not NOTIFICATION_AVAILABLE:
            logger.warning("Desktop notifications not available - install win10toast or plyer")
    
    def send_notification(
        self, 
        title: str, 
        message: str, 
        duration: int = 10,
        icon_path: Optional[str] = None
    ):
        """
        Send desktop notification.
        
        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds
            icon_path: Path to icon (optional)
        """
        if not self.enabled:
            logger.debug(f"Alert suppressed: {title}")
            return
        
        try:
            if notify_func == 'win10toast':
                # Windows 10 toast notification
                toaster.show_toast(
                    title=title,
                    msg=message,
                    duration=duration,
                    icon_path=icon_path,
                    threaded=True
                )
            elif notify_func == 'plyer':
                # Cross-platform notification
                notification.notify(
                    title=title,
                    message=message,
                    timeout=duration
                )
            
            # Log alert
            self.alert_history.append({
                'timestamp': datetime.now().isoformat(),
                'title': title,
                'message': message
            })
            
            # Trim history
            if len(self.alert_history) > self.max_history:
                self.alert_history = self.alert_history[-self.max_history:]
            
            logger.info(f"[ALERT] {title}: {message}")
        
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def alert_news_event(
        self, 
        symbol: str, 
        event_type: str, 
        description: str,
        impact: str = 'high'
    ):
        """
        Alert for high-impact news event.
        
        Args:
            symbol: Stock symbol
            event_type: IPO, M&A, Regulatory, etc.
            description: Event description
            impact: high, medium, low
        """
        if impact == 'high':
            emoji = "🚨"
            duration = 15
        elif impact == 'medium':
            emoji = "⚠️"
            duration = 10
        else:
            emoji = "ℹ️"
            duration = 5
        
        title = f"{emoji} {event_type}: {symbol}"
        message = description[:200]  # Truncate long messages
        
        self.send_notification(title, message, duration=duration)
    
    def alert_sizzle_stock(
        self, 
        symbol: str, 
        metric: str,
        value: float,
        threshold: float
    ):
        """
        Alert for sizzle stock (unusual volume/price move).
        
        Args:
            symbol: Stock symbol
            metric: 'volume', 'price_change', 'momentum'
            value: Current value
            threshold: Threshold that triggered alert
        """
        emoji_map = {
            'volume': '📊',
            'price_change': '📈',
            'momentum': '🚀'
        }
        
        emoji = emoji_map.get(metric, '🔥')
        
        if metric == 'volume':
            title = f"{emoji} SIZZLE ALERT: {symbol}"
            message = f"Volume spike: {value:.0f}x average (threshold: {threshold}x)"
        elif metric == 'price_change':
            title = f"{emoji} BIG MOVER: {symbol}"
            message = f"Price change: {value:+.1f}% (threshold: {threshold:.1f}%)"
        elif metric == 'momentum':
            title = f"{emoji} MOMENTUM SURGE: {symbol}"
            message = f"Momentum score: {value:.2f} (threshold: {threshold:.2f})"
        else:
            title = f"{emoji} ALERT: {symbol}"
            message = f"{metric}: {value} (threshold: {threshold})"
        
        self.send_notification(title, message, duration=12)
    
    def alert_trade_filter_block(
        self,
        symbol: str,
        reason: str,
        filter_type: str
    ):
        """
        Alert when trade is blocked by filter.
        
        Args:
            symbol: Stock symbol
            reason: Why trade was blocked
            filter_type: earnings, macro, news, sentiment, options
        """
        emoji_map = {
            'earnings': '📊',
            'macro': '🏦',
            'news': '📰',
            'sentiment': '😱',
            'options': '🎯'
        }
        
        emoji = emoji_map.get(filter_type, '🛑')
        
        title = f"{emoji} Trade Blocked: {symbol}"
        message = f"{filter_type.upper()} Filter: {reason}"
        
        self.send_notification(title, message, duration=8)
    
    def alert_trade_executed(
        self,
        symbol: str,
        action: str,
        price: float,
        quantity: int
    ):
        """
        Alert when trade is executed.
        
        Args:
            symbol: Stock symbol
            action: BUY, SELL, SHORT, COVER
            price: Execution price
            quantity: Number of shares
        """
        if action in ['BUY', 'SHORT']:
            emoji = '✅'
        else:
            emoji = '💰'
        
        title = f"{emoji} Trade Executed: {symbol}"
        message = f"{action} {quantity} shares @ ${price:.2f}"
        
        self.send_notification(title, message, duration=6)
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict]:
        """Get recent alert history."""
        return self.alert_history[-count:]
    
    def clear_history(self):
        """Clear alert history."""
        self.alert_history = []
        logger.info("Alert history cleared")


class SizzleDetector:
    """
    Detect sizzle stocks (unusual volume, big price moves).
    """
    
    def __init__(
        self,
        volume_threshold: float = 3.0,  # 3x average volume
        price_change_threshold: float = 5.0,  # 5% price change
        momentum_threshold: float = 0.7  # Momentum score > 0.7
    ):
        """
        Initialize sizzle detector.
        
        Args:
            volume_threshold: Volume multiplier (e.g., 3.0 = 3x average)
            price_change_threshold: Price change % to trigger alert
            momentum_threshold: Momentum score threshold
        """
        self.volume_threshold = volume_threshold
        self.price_change_threshold = price_change_threshold
        self.momentum_threshold = momentum_threshold
        
        self.baseline_volumes: Dict[str, float] = {}  # symbol -> avg volume
        self.last_prices: Dict[str, float] = {}  # symbol -> last price
        
        logger.info(f"Sizzle detector initialized (vol: {volume_threshold}x, price: {price_change_threshold}%)")
    
    def check_volume_spike(
        self,
        symbol: str,
        current_volume: float,
        average_volume: Optional[float] = None
    ) -> tuple[bool, float]:
        """
        Check if volume is spiking.
        
        Args:
            symbol: Stock symbol
            current_volume: Current volume
            average_volume: Average volume (optional, uses baseline if None)
        
        Returns:
            (is_sizzle, volume_multiplier)
        """
        if average_volume is None:
            average_volume = self.baseline_volumes.get(symbol, current_volume)
        
        # Update baseline
        self.baseline_volumes[symbol] = average_volume
        
        if average_volume == 0:
            return False, 0.0
        
        multiplier = current_volume / average_volume
        is_sizzle = multiplier >= self.volume_threshold
        
        return is_sizzle, multiplier
    
    def check_price_change(
        self,
        symbol: str,
        current_price: float,
        previous_price: Optional[float] = None
    ) -> tuple[bool, float]:
        """
        Check if price is moving significantly.
        
        Args:
            symbol: Stock symbol
            current_price: Current price
            previous_price: Previous price (optional, uses last known)
        
        Returns:
            (is_sizzle, price_change_percent)
        """
        if previous_price is None:
            previous_price = self.last_prices.get(symbol, current_price)
        
        # Update last price
        self.last_prices[symbol] = current_price
        
        if previous_price == 0:
            return False, 0.0
        
        change_pct = ((current_price - previous_price) / previous_price) * 100
        is_sizzle = abs(change_pct) >= self.price_change_threshold
        
        return is_sizzle, change_pct
    
    def check_momentum(
        self,
        symbol: str,
        momentum_score: float
    ) -> bool:
        """
        Check if momentum is strong.
        
        Args:
            symbol: Stock symbol
            momentum_score: Momentum score (0-1, higher is stronger)
        
        Returns:
            is_sizzle
        """
        return momentum_score >= self.momentum_threshold


# Global alert manager instance
_alert_manager = None


def get_alert_manager(enabled: bool = True) -> AlertManager:
    """Get global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(enabled=enabled)
    return _alert_manager


# Convenience functions
def alert_news(symbol: str, event_type: str, description: str, impact: str = 'high'):
    """Send news event alert."""
    manager = get_alert_manager()
    manager.alert_news_event(symbol, event_type, description, impact)


def alert_sizzle(symbol: str, metric: str, value: float, threshold: float):
    """Send sizzle stock alert."""
    manager = get_alert_manager()
    manager.alert_sizzle_stock(symbol, metric, value, threshold)


def alert_trade_blocked(symbol: str, reason: str, filter_type: str):
    """Send trade block alert."""
    manager = get_alert_manager()
    manager.alert_trade_filter_block(symbol, reason, filter_type)


def alert_trade(symbol: str, action: str, price: float, quantity: int):
    """Send trade execution alert."""
    manager = get_alert_manager()
    manager.alert_trade_executed(symbol, action, price, quantity)
