#!/usr/bin/env python3
"""
Advanced Order Types for market-pie5-bot

Implements various order types beyond basic market orders:
- Limit Orders: Buy/sell at specific price or better
- Stop Orders: Trigger market order when price reaches stop price
- Stop-Limit Orders: Trigger limit order when price reaches stop price
- Trailing Stop Orders: Dynamic stop that follows price movement
- OCO Orders: One-Cancels-Other (two orders, one executes, other cancels)
- Bracket Orders: Entry order with automatic profit target and stop loss
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    OCO = "OCO"  # One-Cancels-Other
    BRACKET = "BRACKET"


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Order:
    """
    Base order class representing a trading order
    """
    
    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType,
        order_id: Optional[str] = None
    ):
        """
        Initialize order
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            side: BUY or SELL
            quantity: Number of shares
            order_type: Type of order
            order_id: Unique order identifier (auto-generated if not provided)
        """
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.order_id = order_id or self._generate_order_id()
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.filled_quantity = 0.0
        self.filled_price = None
        self.filled_at = None
        
        logger.info(f"Created {order_type.value} order: {self.order_id} - {side.value} {quantity} {symbol}")
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"ORD-{timestamp}"
    
    def to_dict(self) -> Dict:
        """Convert order to dictionary"""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price,
            'filled_at': self.filled_at.isoformat() if self.filled_at else None
        }


class MarketOrder(Order):
    """
    Market Order: Execute immediately at current market price
    """
    
    def __init__(self, symbol: str, side: OrderSide, quantity: float):
        super().__init__(symbol, side, quantity, OrderType.MARKET)


class LimitOrder(Order):
    """
    Limit Order: Execute at specified price or better
    - BUY limit: Execute at limit price or lower
    - SELL limit: Execute at limit price or higher
    """
    
    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        limit_price: float,
        time_in_force: str = "DAY"
    ):
        """
        Initialize limit order
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares
            limit_price: Maximum buy price or minimum sell price
            time_in_force: Order duration (DAY, GTC, IOC, FOK)
        """
        super().__init__(symbol, side, quantity, OrderType.LIMIT)
        self.limit_price = limit_price
        self.time_in_force = time_in_force
        
        logger.info(f"Limit order details: price=${limit_price:.2f}, TIF={time_in_force}")
    
    def can_execute(self, current_price: float) -> bool:
        """
        Check if order can execute at current price
        
        Args:
            current_price: Current market price
            
        Returns:
            True if order can execute, False otherwise
        """
        if self.status != OrderStatus.ACTIVE:
            return False
        
        if self.side == OrderSide.BUY:
            # BUY limit: execute if current price <= limit price
            return current_price <= self.limit_price
        else:
            # SELL limit: execute if current price >= limit price
            return current_price >= self.limit_price


class StopOrder(Order):
    """
    Stop Order: Becomes market order when stop price is reached
    - BUY stop: Trigger when price rises to stop price
    - SELL stop: Trigger when price falls to stop price
    """
    
    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        stop_price: float
    ):
        """
        Initialize stop order
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares
            stop_price: Price that triggers the order
        """
        super().__init__(symbol, side, quantity, OrderType.STOP)
        self.stop_price = stop_price
        self.triggered = False
        
        logger.info(f"Stop order details: stop_price=${stop_price:.2f}")
    
    def check_trigger(self, current_price: float) -> bool:
        """
        Check if stop price has been reached
        
        Args:
            current_price: Current market price
            
        Returns:
            True if stop triggered, False otherwise
        """
        if self.triggered or self.status != OrderStatus.ACTIVE:
            return self.triggered
        
        if self.side == OrderSide.BUY:
            # BUY stop: trigger when price rises to stop price
            self.triggered = current_price >= self.stop_price
        else:
            # SELL stop: trigger when price falls to stop price
            self.triggered = current_price <= self.stop_price
        
        if self.triggered:
            logger.info(f"Stop order {self.order_id} triggered at ${current_price:.2f}")
        
        return self.triggered


class StopLimitOrder(Order):
    """
    Stop-Limit Order: Becomes limit order when stop price is reached
    Combines stop order trigger with limit order execution
    """
    
    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        stop_price: float,
        limit_price: float
    ):
        """
        Initialize stop-limit order
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares
            stop_price: Price that triggers the order
            limit_price: Limit price after trigger
        """
        super().__init__(symbol, side, quantity, OrderType.STOP_LIMIT)
        self.stop_price = stop_price
        self.limit_price = limit_price
        self.triggered = False
        
        logger.info(f"Stop-limit order: stop=${stop_price:.2f}, limit=${limit_price:.2f}")
    
    def check_trigger(self, current_price: float) -> bool:
        """Check if stop price has been reached"""
        if self.triggered or self.status != OrderStatus.ACTIVE:
            return self.triggered
        
        if self.side == OrderSide.BUY:
            self.triggered = current_price >= self.stop_price
        else:
            self.triggered = current_price <= self.stop_price
        
        if self.triggered:
            logger.info(f"Stop-limit order {self.order_id} triggered at ${current_price:.2f}")
        
        return self.triggered
    
    def can_execute(self, current_price: float) -> bool:
        """Check if order can execute at current price (after trigger)"""
        if not self.triggered or self.status != OrderStatus.ACTIVE:
            return False
        
        if self.side == OrderSide.BUY:
            return current_price <= self.limit_price
        else:
            return current_price >= self.limit_price


class TrailingStopOrder(Order):
    """
    Trailing Stop Order: Dynamic stop that follows favorable price movement
    - BUY: Stop rises as price falls (for short positions)
    - SELL: Stop falls as price rises (for long positions)
    """
    
    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        trail_amount: Optional[float] = None,
        trail_percent: Optional[float] = None
    ):
        """
        Initialize trailing stop order
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares
            trail_amount: Fixed dollar amount trail (e.g., $2.00)
            trail_percent: Percentage trail (e.g., 0.03 for 3%)
            
        Note: Provide either trail_amount or trail_percent, not both
        """
        super().__init__(symbol, side, quantity, OrderType.TRAILING_STOP)
        
        if (trail_amount is not None) and (trail_percent is not None):
            raise ValueError("Provide either trail_amount or trail_percent, not both")
        if (trail_amount is None) and (trail_percent is None):
            raise ValueError("Must provide either trail_amount or trail_percent")
        
        self.trail_amount = trail_amount
        self.trail_percent = trail_percent
        self.high_water_mark = None  # For SELL orders
        self.low_water_mark = None   # For BUY orders
        self.current_stop_price = None
        self.triggered = False
        
        logger.info(f"Trailing stop order: amount=${trail_amount} percent={trail_percent}")
    
    def update_stop(self, current_price: float):
        """
        Update trailing stop price based on current price
        
        Args:
            current_price: Current market price
        """
        if self.status != OrderStatus.ACTIVE:
            return
        
        if self.side == OrderSide.SELL:
            # For SELL (long position): track high and trail below
            if self.high_water_mark is None or current_price > self.high_water_mark:
                self.high_water_mark = current_price
                
                if self.trail_amount:
                    self.current_stop_price = self.high_water_mark - self.trail_amount
                else:
                    self.current_stop_price = self.high_water_mark * (1 - self.trail_percent)
                
                logger.debug(f"Updated trailing stop: high=${self.high_water_mark:.2f}, stop=${self.current_stop_price:.2f}")
        
        else:  # BUY (short position)
            # For BUY (short position): track low and trail above
            if self.low_water_mark is None or current_price < self.low_water_mark:
                self.low_water_mark = current_price
                
                if self.trail_amount:
                    self.current_stop_price = self.low_water_mark + self.trail_amount
                else:
                    self.current_stop_price = self.low_water_mark * (1 + self.trail_percent)
                
                logger.debug(f"Updated trailing stop: low=${self.low_water_mark:.2f}, stop=${self.current_stop_price:.2f}")
    
    def check_trigger(self, current_price: float) -> bool:
        """Check if trailing stop has been triggered"""
        self.update_stop(current_price)
        
        if self.triggered or self.status != OrderStatus.ACTIVE or self.current_stop_price is None:
            return self.triggered
        
        if self.side == OrderSide.SELL:
            # SELL trailing stop: trigger when price falls below stop
            self.triggered = current_price <= self.current_stop_price
        else:
            # BUY trailing stop: trigger when price rises above stop
            self.triggered = current_price >= self.current_stop_price
        
        if self.triggered:
            logger.info(f"Trailing stop order {self.order_id} triggered at ${current_price:.2f}")
        
        return self.triggered


class OCOOrder:
    """
    One-Cancels-Other (OCO) Order: Two orders where execution of one cancels the other
    Typically used for take-profit and stop-loss combination
    """
    
    def __init__(self, order1: Order, order2: Order):
        """
        Initialize OCO order
        
        Args:
            order1: First order (e.g., take-profit limit)
            order2: Second order (e.g., stop-loss)
        """
        self.order1 = order1
        self.order2 = order2
        self.oco_id = self._generate_oco_id()
        self.active = True
        
        logger.info(f"Created OCO order: {self.oco_id}")
        logger.info(f"  Order 1: {order1.order_type.value} {order1.side.value} {order1.symbol}")
        logger.info(f"  Order 2: {order2.order_type.value} {order2.side.value} {order2.symbol}")
    
    def _generate_oco_id(self) -> str:
        """Generate unique OCO ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"OCO-{timestamp}"
    
    def cancel_other(self, filled_order: Order):
        """
        Cancel the other order when one is filled
        
        Args:
            filled_order: The order that was filled
        """
        if filled_order == self.order1:
            self.order2.status = OrderStatus.CANCELLED
            logger.info(f"OCO: Order 1 filled, cancelled Order 2 ({self.order2.order_id})")
        else:
            self.order1.status = OrderStatus.CANCELLED
            logger.info(f"OCO: Order 2 filled, cancelled Order 1 ({self.order1.order_id})")
        
        self.active = False


class BracketOrder:
    """
    Bracket Order: Entry order with automatic take-profit and stop-loss
    Creates three orders:
    1. Entry order (market or limit)
    2. Take-profit limit order
    3. Stop-loss order
    """
    
    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        entry_price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        take_profit_percent: Optional[float] = None,
        stop_loss_percent: Optional[float] = None
    ):
        """
        Initialize bracket order
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares
            entry_price: Entry limit price (None for market order)
            take_profit_price: Absolute take-profit price
            stop_loss_price: Absolute stop-loss price
            take_profit_percent: Take-profit as percentage (e.g., 0.05 for 5%)
            stop_loss_percent: Stop-loss as percentage (e.g., 0.03 for 3%)
            
        Note: Provide either absolute prices or percentages, not both
        """
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.bracket_id = self._generate_bracket_id()
        
        # Create entry order
        if entry_price:
            self.entry_order = LimitOrder(symbol, side, quantity, entry_price)
        else:
            self.entry_order = MarketOrder(symbol, side, quantity)
        
        # Calculate profit/loss levels
        if (take_profit_price is not None) and (stop_loss_price is not None):
            self.take_profit_price = take_profit_price
            self.stop_loss_price = stop_loss_price
        elif (take_profit_percent is not None) and (stop_loss_percent is not None) and (entry_price is not None):
            if side == OrderSide.BUY:
                self.take_profit_price = entry_price * (1 + take_profit_percent)
                self.stop_loss_price = entry_price * (1 - stop_loss_percent)
            else:
                self.take_profit_price = entry_price * (1 - take_profit_percent)
                self.stop_loss_price = entry_price * (1 + stop_loss_percent)
        else:
            raise ValueError("Must provide either absolute prices or percentages with entry_price")
        
        # Create exit orders (will be activated after entry fills)
        exit_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
        self.take_profit_order = LimitOrder(symbol, exit_side, quantity, self.take_profit_price)
        self.stop_loss_order = StopOrder(symbol, exit_side, quantity, self.stop_loss_price)
        
        # Set exit orders to pending (activate after entry fills)
        self.take_profit_order.status = OrderStatus.PENDING
        self.stop_loss_order.status = OrderStatus.PENDING
        
        # Create OCO for exit orders
        self.exit_oco = OCOOrder(self.take_profit_order, self.stop_loss_order)
        
        logger.info(f"Created bracket order: {self.bracket_id}")
        logger.info(f"  Entry: {entry_price if entry_price else 'MARKET'}")
        logger.info(f"  Take-profit: ${self.take_profit_price:.2f}")
        logger.info(f"  Stop-loss: ${self.stop_loss_price:.2f}")
    
    def _generate_bracket_id(self) -> str:
        """Generate unique bracket ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"BRACKET-{timestamp}"
    
    def activate_exit_orders(self):
        """Activate exit orders after entry order fills"""
        self.take_profit_order.status = OrderStatus.ACTIVE
        self.stop_loss_order.status = OrderStatus.ACTIVE
        logger.info(f"Activated exit orders for bracket {self.bracket_id}")


class OrderManager:
    """
    Manages all orders and handles order execution logic
    """
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.oco_orders: List[OCOOrder] = []
        self.bracket_orders: List[BracketOrder] = []
        
        logger.info("Initialized OrderManager")
    
    def submit_order(self, order: Order) -> str:
        """
        Submit an order for execution
        
        Args:
            order: Order to submit
            
        Returns:
            Order ID
        """
        order.status = OrderStatus.ACTIVE
        self.orders[order.order_id] = order
        
        logger.info(f"Submitted order: {order.order_id}")
        return order.order_id
    
    def submit_oco(self, oco: OCOOrder) -> str:
        """Submit OCO order"""
        self.submit_order(oco.order1)
        self.submit_order(oco.order2)
        self.oco_orders.append(oco)
        
        logger.info(f"Submitted OCO: {oco.oco_id}")
        return oco.oco_id
    
    def submit_bracket(self, bracket: BracketOrder) -> str:
        """Submit bracket order"""
        self.submit_order(bracket.entry_order)
        self.bracket_orders.append(bracket)
        
        logger.info(f"Submitted bracket: {bracket.bracket_id}")
        return bracket.bracket_id
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancelled, False otherwise
        """
        if order_id not in self.orders:
            logger.warning(f"Order not found: {order_id}")
            return False
        
        order = self.orders[order_id]
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            logger.warning(f"Cannot cancel order {order_id}: status={order.status.value}")
            return False
        
        order.status = OrderStatus.CANCELLED
        logger.info(f"Cancelled order: {order_id}")
        return True
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_active_orders(self) -> List[Order]:
        """Get all active orders"""
        return [o for o in self.orders.values() if o.status == OrderStatus.ACTIVE]
    
    def process_orders(self, current_prices: Dict[str, float]):
        """
        Process all active orders against current prices
        
        Args:
            current_prices: Dictionary of symbol -> current price
        """
        for order in self.get_active_orders():
            if order.symbol not in current_prices:
                continue
            
            current_price = current_prices[order.symbol]
            
            # Handle different order types
            if isinstance(order, MarketOrder):
                self._execute_order(order, current_price)
            
            elif isinstance(order, LimitOrder):
                if order.can_execute(current_price):
                    self._execute_order(order, order.limit_price)
            
            elif isinstance(order, (StopOrder, StopLimitOrder)):
                if order.check_trigger(current_price):
                    if isinstance(order, StopOrder):
                        self._execute_order(order, current_price)
                    elif isinstance(order, StopLimitOrder) and order.can_execute(current_price):
                        self._execute_order(order, order.limit_price)
            
            elif isinstance(order, TrailingStopOrder):
                if order.check_trigger(current_price):
                    self._execute_order(order, current_price)
    
    def _execute_order(self, order: Order, execution_price: float):
        """Execute an order"""
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = execution_price
        order.filled_at = datetime.now()
        
        logger.info(f"Executed order {order.order_id}: {order.quantity} @ ${execution_price:.2f}")
        
        # Handle OCO orders
        for oco in self.oco_orders:
            if oco.active and (order == oco.order1 or order == oco.order2):
                oco.cancel_other(order)
        
        # Handle bracket orders
        for bracket in self.bracket_orders:
            if order == bracket.entry_order and order.status == OrderStatus.FILLED:
                bracket.activate_exit_orders()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Advanced Order Types Module - Example Usage")
    print("="*60)
    
    # Create order manager
    manager = OrderManager()
    
    # Example 1: Limit order
    print("\n--- Example 1: Limit Order ---")
    limit_order = LimitOrder("AAPL", OrderSide.BUY, 10, limit_price=150.00)
    manager.submit_order(limit_order)
    
    # Example 2: Stop-limit order
    print("\n--- Example 2: Stop-Limit Order ---")
    stop_limit = StopLimitOrder("MSFT", OrderSide.SELL, 5, stop_price=380.00, limit_price=375.00)
    manager.submit_order(stop_limit)
    
    # Example 3: Trailing stop order
    print("\n--- Example 3: Trailing Stop Order ---")
    trailing_stop = TrailingStopOrder("GOOGL", OrderSide.SELL, 8, trail_percent=0.03)
    manager.submit_order(trailing_stop)
    
    # Example 4: OCO order
    print("\n--- Example 4: OCO Order ---")
    take_profit = LimitOrder("TSLA", OrderSide.SELL, 10, limit_price=250.00)
    stop_loss = StopOrder("TSLA", OrderSide.SELL, 10, stop_price=200.00)
    oco = OCOOrder(take_profit, stop_loss)
    manager.submit_oco(oco)
    
    # Example 5: Bracket order
    print("\n--- Example 5: Bracket Order ---")
    bracket = BracketOrder(
        symbol="NVDA",
        side=OrderSide.BUY,
        quantity=15,
        entry_price=500.00,
        take_profit_price=525.00,
        stop_loss_price=485.00
    )
    manager.submit_bracket(bracket)
    
    print("\n" + "="*60)
    print(f"Total active orders: {len(manager.get_active_orders())}")
    print("="*60)
