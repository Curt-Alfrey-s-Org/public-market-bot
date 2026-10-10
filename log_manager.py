#!/usr/bin/env python3
"""
Centralized Log Management System for market-pie5-bot
Consolidates logging from multiple sources: log_queue, trade_history, and backtesting reports
REFACTORED: Now uses SQLAlchemy ORM instead of raw sqlite3 for PostgreSQL compatibility
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import Session
from database import Base, SessionLocal, engine
import os


# ============================================================================
# SQLAlchemy Models for Trading Logs
# ============================================================================

class TradeLog(Base):
    """Trade log ORM model"""
    __tablename__ = 'trades'
    __table_args__ = {'schema': 'trading' if os.getenv('DATABASE_URL', '').startswith('postgresql') else None}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)
    quantity = Column(Float)
    price = Column(Float)
    is_win = Column(Integer)
    pnl = Column(Float)
    pnl_percent = Column(Float)
    entry_price = Column(Float)
    exit_price = Column(Float)
    exit_reason = Column(String)
    strategy = Column(String)
    trade_metadata = Column(Text)  # JSON string


class SystemLog(Base):
    """System log ORM model"""
    __tablename__ = 'system_logs'
    __table_args__ = {'schema': 'trading' if os.getenv('DATABASE_URL', '').startswith('postgresql') else None}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    level = Column(String)
    message = Column(Text)
    log_metadata = Column(Text)  # JSON string


class BacktestResult(Base):
    """Backtest results ORM model"""
    __tablename__ = 'backtest_results'
    __table_args__ = {'schema': 'trading' if os.getenv('DATABASE_URL', '').startswith('postgresql') else None}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    initial_capital = Column(Float)
    final_capital = Column(Float)
    total_pnl = Column(Float)
    roi = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    strategy = Column(String)
    backtest_metadata = Column(Text)  # JSON string


class PerformanceMetric(Base):
    """Performance metrics ORM model"""
    __tablename__ = 'performance_metrics'
    __table_args__ = {'schema': 'trading' if os.getenv('DATABASE_URL', '').startswith('postgresql') else None}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    metric_name = Column(String)
    metric_value = Column(Float)
    metric_metadata = Column(Text)  # JSON string


# ============================================================================
# LogManager Class
# ============================================================================

class LogManager:
    """
    Unified logging system that consolidates logs from different sources
    and provides storage in both JSON and SQLite/PostgreSQL formats
    """
    
    def __init__(self, log_dir: str = "logs", db_name: str = "trading_logs.db"):
        """
        Initialize the log manager
        
        Args:
            log_dir: Directory to store log files
            db_name: Name of database file (unused for PostgreSQL, kept for compatibility)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize database tables
        self._init_database()
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _init_database(self):
        """Initialize database schema using SQLAlchemy"""
        # Create all tables defined in Base.metadata
        Base.metadata.create_all(bind=engine)
    
    def log_trade(self, trade_data: Dict[str, Any], session_id: Optional[str] = None):
        """
        Log a trade to both JSON and database storage
        
        Args:
            trade_data: Dictionary containing trade information
            session_id: Optional session identifier
        """
        if session_id is None:
            session_id = self.session_id
        
        # Parse timestamp
        timestamp_str = trade_data.get('timestamp')
        if timestamp_str:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = timestamp_str
        else:
            timestamp = datetime.now()
        
        # Create trade log entry
        trade_log = TradeLog(
            session_id=session_id,
            timestamp=timestamp,
            symbol=trade_data.get('symbol'),
            action=trade_data.get('action'),
            quantity=trade_data.get('quantity'),
            price=trade_data.get('price'),
            is_win=1 if trade_data.get('is_win') else 0,
            pnl=trade_data.get('pnl'),
            pnl_percent=trade_data.get('pnl_percent'),
            entry_price=trade_data.get('entry_price'),
            exit_price=trade_data.get('exit_price'),
            exit_reason=trade_data.get('exit_reason', 'unknown'),
            strategy=trade_data.get('strategy', 'default'),
            trade_metadata=json.dumps(trade_data.get('metadata', {}))
        )
        
        # Store in database
        db: Session = SessionLocal()
        try:
            db.add(trade_log)
            db.commit()
        finally:
            db.close()
        
        # Also append to JSON file for easy viewing
        json_file = self.log_dir / f"trades_{session_id}.json"
        self._append_to_json(json_file, trade_data)
    
    def log_system_event(self, level: str, message: str, metadata: Optional[Dict] = None):
        """
        Log a system event
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            metadata: Optional metadata dictionary
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'metadata': metadata or {}
        }
        
        # Create system log entry
        system_log = SystemLog(
            session_id=self.session_id,
            timestamp=datetime.now(),
            level=level,
            message=message,
            log_metadata=json.dumps(metadata or {})
        )
        
        # Store in database
        db: Session = SessionLocal()
        try:
            db.add(system_log)
            db.commit()
        finally:
            db.close()
        
        # Also append to JSON file
        json_file = self.log_dir / f"system_{self.session_id}.json"
        self._append_to_json(json_file, log_entry)
    
    def log_backtest_result(self, backtest_data: Dict[str, Any]):
        """
        Log backtest results
        
        Args:
            backtest_data: Dictionary containing backtest results
        """
        timestamp = datetime.now()
        
        # Create backtest result entry
        backtest_result = BacktestResult(
            session_id=self.session_id,
            timestamp=timestamp,
            initial_capital=backtest_data.get('initial_capital'),
            final_capital=backtest_data.get('final_capital'),
            total_pnl=backtest_data.get('total_pnl'),
            roi=backtest_data.get('roi'),
            total_trades=backtest_data.get('total_trades'),
            winning_trades=backtest_data.get('winning_trades'),
            losing_trades=backtest_data.get('losing_trades'),
            win_rate=backtest_data.get('win_rate'),
            strategy=backtest_data.get('strategy', 'default'),
            backtest_metadata=json.dumps(backtest_data.get('metadata', {}))
        )
        
        # Store in database
        db: Session = SessionLocal()
        try:
            db.add(backtest_result)
            db.commit()
        finally:
            db.close()
        
        # Store complete results in JSON
        json_file = self.log_dir / f"backtest_{self.session_id}.json"
        self._save_to_json(json_file, backtest_data)
    
    def log_performance_metric(self, metric_name: str, metric_value: float, 
                               metadata: Optional[Dict] = None):
        """
        Log a performance metric
        
        Args:
            metric_name: Name of the metric (e.g., 'sharpe_ratio', 'max_drawdown')
            metric_value: Value of the metric
            metadata: Optional metadata
        """
        # Create performance metric entry
        perf_metric = PerformanceMetric(
            session_id=self.session_id,
            timestamp=datetime.now(),
            metric_name=metric_name,
            metric_value=metric_value,
            metric_metadata=json.dumps(metadata or {})
        )
        
        # Store in database
        db: Session = SessionLocal()
        try:
            db.add(perf_metric)
            db.commit()
        finally:
            db.close()
    
    def merge_trade_history(self, trade_history: List[Dict]) -> int:
        """
        Merge existing trade history into the log system
        
        Args:
            trade_history: List of trade dictionaries
            
        Returns:
            Number of trades merged
        """
        for trade in trade_history:
            self.log_trade(trade)
        
        return len(trade_history)
    
    def get_trades(self, session_id: Optional[str] = None, 
                   symbol: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> List[Dict]:
        """
        Retrieve trades with optional filters
        
        Args:
            session_id: Filter by session ID
            symbol: Filter by symbol
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            
        Returns:
            List of trade dictionaries
        """
        db: Session = SessionLocal()
        try:
            query = db.query(TradeLog)
            
            if session_id:
                query = query.filter(TradeLog.session_id == session_id)
            
            if symbol:
                query = query.filter(TradeLog.symbol == symbol)
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(TradeLog.timestamp >= start_dt)
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(TradeLog.timestamp <= end_dt)
            
            query = query.order_by(TradeLog.timestamp)
            
            trades = query.all()
            
            # Convert to dictionaries
            return [
                {
                    'id': t.id,
                    'session_id': t.session_id,
                    'timestamp': t.timestamp.isoformat() if t.timestamp else None,
                    'symbol': t.symbol,
                    'action': t.action,
                    'quantity': t.quantity,
                    'price': t.price,
                    'is_win': t.is_win,
                    'pnl': t.pnl,
                    'pnl_percent': t.pnl_percent,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'exit_reason': t.exit_reason,
                    'strategy': t.strategy,
                    'metadata': t.trade_metadata
                }
                for t in trades
            ]
        finally:
            db.close()
    
    def get_backtest_results(self, session_id: Optional[str] = None) -> List[Dict]:
        """
        Retrieve backtest results
        
        Args:
            session_id: Optional session ID filter
            
        Returns:
            List of backtest result dictionaries
        """
        db: Session = SessionLocal()
        try:
            query = db.query(BacktestResult)
            
            if session_id:
                query = query.filter(BacktestResult.session_id == session_id)
            
            query = query.order_by(BacktestResult.timestamp)
            results = query.all()
            
            # Convert to dictionaries
            return [
                {
                    'id': r.id,
                    'session_id': r.session_id,
                    'timestamp': r.timestamp.isoformat() if r.timestamp else None,
                    'initial_capital': r.initial_capital,
                    'final_capital': r.final_capital,
                    'total_pnl': r.total_pnl,
                    'roi': r.roi,
                    'total_trades': r.total_trades,
                    'winning_trades': r.winning_trades,
                    'losing_trades': r.losing_trades,
                    'win_rate': r.win_rate,
                    'strategy': r.strategy,
                    'metadata': r.backtest_metadata
                }
                for r in results
            ]
        finally:
            db.close()
    
    def _append_to_json(self, file_path: Path, data: Dict):
        """Append data to a JSON file as a new line"""
        with open(file_path, 'a') as f:
            f.write(json.dumps(data, default=str) + '\n')
    
    def _save_to_json(self, file_path: Path, data: Dict):
        """Save data to a JSON file (overwrite)"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    # --- Reset helpers ---
    def clear_trades(self, session_only: bool = False, session_id: Optional[str] = None) -> int:
        """Clear trades from database. If session_only and session_id provided, only clear that session.
        Returns number of rows affected.
        """
        db: Session = SessionLocal()
        try:
            query = db.query(TradeLog)
            
            if session_only and session_id:
                query = query.filter(TradeLog.session_id == session_id)
            
            affected = query.delete()
            db.commit()
            return affected
        finally:
            db.close()

    def clear_system_logs(self, session_only: bool = False, session_id: Optional[str] = None) -> int:
        """Clear system logs from database. Returns number of rows affected."""
        db: Session = SessionLocal()
        try:
            query = db.query(SystemLog)
            
            if session_only and session_id:
                query = query.filter(SystemLog.session_id == session_id)
            
            affected = query.delete()
            db.commit()
            return affected
        finally:
            db.close()


if __name__ == "__main__":
    # Example usage
    print("Log Manager Example Usage")
    print("=" * 60)
    
    # Create log manager
    log_manager = LogManager()
    
    # Log a trade
    trade = {
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 10.0,
        'price': 150.0,
        'is_win': True,
        'pnl': 50.0,
        'pnl_percent': 3.33,
        'exit_reason': 'trailing_stop',
        'strategy': 'momentum'
    }
    log_manager.log_trade(trade)
    print(f"✓ Logged trade: {trade['symbol']} {trade['action']}")
    
    # Log a system event
    log_manager.log_system_event('INFO', 'Trading bot started', {'version': '1.0'})
    print("✓ Logged system event")
    
    # Log backtest result
    backtest = {
        'initial_capital': 10000.0,
        'final_capital': 11000.0,
        'total_pnl': 1000.0,
        'roi': 0.10,
        'total_trades': 50,
        'winning_trades': 30,
        'losing_trades': 20,
        'win_rate': 0.60
    }
    log_manager.log_backtest_result(backtest)
    print("✓ Logged backtest result")
    
    # Retrieve trades
    trades = log_manager.get_trades()
    print(f"\n✓ Retrieved {len(trades)} trades from database")
    
    print("\nLog files created in 'logs' directory:")
    for file in log_manager.log_dir.glob("*"):
        print(f"  - {file.name}")
    
    def log_trade(self, trade_data: Dict[str, Any], session_id: Optional[str] = None):
        """
        Log a trade to both JSON and SQLite storage
        
        Args:
            trade_data: Dictionary containing trade information
            session_id: Optional session identifier
        """
        if session_id is None:
            session_id = self.session_id
        
        # Add timestamp if not present
        if 'timestamp' not in trade_data:
            trade_data['timestamp'] = datetime.now().isoformat()
        
        # Store in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trades (
                session_id, timestamp, symbol, action, quantity, price,
                is_win, pnl, pnl_percent, entry_price, exit_price,
                exit_reason, strategy, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            trade_data.get('timestamp'),
            trade_data.get('symbol'),
            trade_data.get('action'),
            trade_data.get('quantity'),
            trade_data.get('price'),
            1 if trade_data.get('is_win') else 0,
            trade_data.get('pnl'),
            trade_data.get('pnl_percent'),
            trade_data.get('entry_price'),
            trade_data.get('exit_price'),
            trade_data.get('exit_reason', 'unknown'),
            trade_data.get('strategy', 'default'),
            json.dumps(trade_data.get('metadata', {}))
        ))
        
        conn.commit()
        conn.close()
        
        # Also append to JSON file for easy viewing
        json_file = self.log_dir / f"trades_{session_id}.json"
        self._append_to_json(json_file, trade_data)
    
    def log_system_event(self, level: str, message: str, metadata: Optional[Dict] = None):
        """
        Log a system event
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            metadata: Optional metadata dictionary
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'metadata': metadata or {}
        }
        
        # Store in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_logs (session_id, timestamp, level, message, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.session_id,
            log_entry['timestamp'],
            level,
            message,
            json.dumps(metadata or {})
        ))
        
        conn.commit()
        conn.close()
        
        # Also append to JSON file
        json_file = self.log_dir / f"system_{self.session_id}.json"
        self._append_to_json(json_file, log_entry)
    
    def log_backtest_result(self, backtest_data: Dict[str, Any]):
        """
        Log backtest results
        
        Args:
            backtest_data: Dictionary containing backtest results
        """
        timestamp = datetime.now().isoformat()
        
        # Store in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO backtest_results (
                session_id, timestamp, initial_capital, final_capital,
                total_pnl, roi, total_trades, winning_trades,
                losing_trades, win_rate, strategy, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.session_id,
            timestamp,
            backtest_data.get('initial_capital'),
            backtest_data.get('final_capital'),
            backtest_data.get('total_pnl'),
            backtest_data.get('roi'),
            backtest_data.get('total_trades'),
            backtest_data.get('winning_trades'),
            backtest_data.get('losing_trades'),
            backtest_data.get('win_rate'),
            backtest_data.get('strategy', 'default'),
            json.dumps(backtest_data.get('metadata', {}))
        ))
        
        conn.commit()
        conn.close()
        
        # Store complete results in JSON
        json_file = self.log_dir / f"backtest_{self.session_id}.json"
        self._save_to_json(json_file, backtest_data)
    
    def log_performance_metric(self, metric_name: str, metric_value: float, 
                               metadata: Optional[Dict] = None):
        """
        Log a performance metric
        
        Args:
            metric_name: Name of the metric (e.g., 'sharpe_ratio', 'max_drawdown')
            metric_value: Value of the metric
            metadata: Optional metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO performance_metrics (session_id, timestamp, metric_name, metric_value, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.session_id,
            datetime.now().isoformat(),
            metric_name,
            metric_value,
            json.dumps(metadata or {})
        ))
        
        conn.commit()
        conn.close()
    
    def merge_trade_history(self, trade_history: List[Dict]) -> int:
        """
        Merge existing trade history into the log system
        
        Args:
            trade_history: List of trade dictionaries
            
        Returns:
            Number of trades merged
        """
        for trade in trade_history:
            self.log_trade(trade)
        
        return len(trade_history)
    
    def get_trades(self, session_id: Optional[str] = None, 
                   symbol: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> List[Dict]:
        """
        Retrieve trades with optional filters
        
        Args:
            session_id: Filter by session ID
            symbol: Filter by symbol
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            
        Returns:
            List of trade dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_backtest_results(self, session_id: Optional[str] = None) -> List[Dict]:
        """
        Retrieve backtest results
        
        Args:
            session_id: Optional session ID filter
            
        Returns:
            List of backtest result dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute(
                "SELECT * FROM backtest_results WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            )
        else:
            cursor.execute("SELECT * FROM backtest_results ORDER BY timestamp")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def _append_to_json(self, file_path: Path, data: Dict):
        """Append data to a JSON file as a new line"""
        with open(file_path, 'a') as f:
            f.write(json.dumps(data, default=str) + '\n')
    
    def _save_to_json(self, file_path: Path, data: Dict):
        """Save data to a JSON file (overwrite)"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    # --- Reset helpers ---
    def clear_trades(self, session_only: bool = False, session_id: Optional[str] = None) -> int:
        """Clear trades from SQLite. If session_only and session_id provided, only clear that session.
        Returns number of rows affected (best-effort).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            if session_only and session_id:
                cursor.execute("DELETE FROM trades WHERE session_id = ?", (session_id,))
            else:
                cursor.execute("DELETE FROM trades")
            affected = cursor.rowcount if cursor.rowcount is not None else 0
            conn.commit()
            return affected
        finally:
            conn.close()

    def clear_system_logs(self, session_only: bool = False, session_id: Optional[str] = None) -> int:
        """Clear system logs from SQLite (optional). Returns number of rows affected."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            if session_only and session_id:
                cursor.execute("DELETE FROM system_logs WHERE session_id = ?", (session_id,))
            else:
                cursor.execute("DELETE FROM system_logs")
            affected = cursor.rowcount if cursor.rowcount is not None else 0
            conn.commit()
            return affected
        finally:
            conn.close()


if __name__ == "__main__":
    # Example usage
    print("Log Manager Example Usage")
    print("=" * 60)
    
    # Create log manager
    log_manager = LogManager()
    
    # Log a trade
    trade = {
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 10.0,
        'price': 150.0,
        'is_win': True,
        'pnl': 50.0,
        'pnl_percent': 3.33,
        'exit_reason': 'trailing_stop',
        'strategy': 'momentum'
    }
    log_manager.log_trade(trade)
    print(f"✓ Logged trade: {trade['symbol']} {trade['action']}")
    
    # Log a system event
    log_manager.log_system_event('INFO', 'Trading bot started', {'version': '1.0'})
    print("✓ Logged system event")
    
    # Log backtest result
    backtest = {
        'initial_capital': 10000.0,
        'final_capital': 11000.0,
        'total_pnl': 1000.0,
        'roi': 0.10,
        'total_trades': 50,
        'winning_trades': 30,
        'losing_trades': 20,
        'win_rate': 0.60
    }
    log_manager.log_backtest_result(backtest)
    print("✓ Logged backtest result")
    
    # Retrieve trades
    trades = log_manager.get_trades()
    print(f"\n✓ Retrieved {len(trades)} trades from database")
    
    print("\nLog files created in 'logs' directory:")
    for file in log_manager.log_dir.glob("*"):
        print(f"  - {file.name}")
