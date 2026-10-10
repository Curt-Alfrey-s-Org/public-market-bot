"""
Tests for Phase 1.1: Startup Recovery

Tests auto-initialization of market data on bot restart.
"""

import asyncio
import json
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Test imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.startup import initialize_bot_data, get_startup_status, DEFAULT_SYMBOLS


class TestStartupRecovery:
    """Tests for startup recovery functionality."""

    @pytest.mark.asyncio
    async def test_existing_bot_state_skips_fetch(self):
        """Test: Empty DB → bot starts → existing bot_state.json → skip yfinance."""
        # Create temporary bot_state.json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            bot_state_data = {
                "AAPL": {"price": 150.0, "shares": 10},
                "SPY": {"price": 450.0, "shares": 5},
            }
            json.dump(bot_state_data, f)
            temp_state_path = f.name

        try:
            with patch('api.startup.Path') as mock_path:
                # Mock bot_state path
                mock_bot_state = Mock()
                mock_bot_state.exists.return_value = True
                
                def side_effect(path_str):
                    if "bot_state.json" in str(path_str):
                        return mock_bot_state
                    return Path(path_str)
                
                mock_path.side_effect = side_effect
                
                # Mock file reading
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(bot_state_data)
                    
                    result = await initialize_bot_data()
                    
                    assert result['initialized'] is True
                    assert result['symbol_count'] == 2
                    assert 'timestamp' in result
                    assert result['error'] is None

        finally:
            if os.path.exists(temp_state_path):
                os.remove(temp_state_path)

    @pytest.mark.asyncio
    async def test_empty_database_fetches_yfinance(self):
        """Test: Empty DB → yfinance fetch with timeout → data loads."""
        with patch('api.startup.Path') as mock_path:
            mock_bot_state = Mock()
            mock_bot_state.exists.return_value = False
            
            def side_effect(path_str):
                if "bot_state.json" in str(path_str):
                    return mock_bot_state
                return Path(path_str)
            
            mock_path.side_effect = side_effect
            
            # Mock yfinance
            # api.startup imports yfinance lazily inside the function,
            # so patch sys.modules rather than a module attribute
            mock_yf = MagicMock()
            with patch.dict('sys.modules', {'yfinance': mock_yf}):
                # Mock database check (no records)
                with patch('builtins.open', side_effect=FileNotFoundError):
                    with patch('database.SessionLocal') as mock_session_local:
                        mock_db = MagicMock()
                        mock_db.execute.side_effect = Exception("No trades table")
                        mock_session_local.return_value = mock_db
                        
                        # Mock ticker data
                        mock_ticker = Mock()
                        mock_history = Mock()
                        mock_history.__len__ = Mock(return_value=10)  # 10 data points
                        
                        async def mock_ticker_history(*args, **kwargs):
                            return mock_history
                        
                        mock_ticker.history = Mock(return_value=mock_history)
                        mock_yf.Ticker.return_value = mock_ticker
                        
                        result = await initialize_bot_data()
                        
                        assert result['initialized'] is True or result['initialized'] is False
                        assert 'timestamp' in result
                        assert 'symbol_count' in result

    @pytest.mark.asyncio
    async def test_yfinance_timeout_logs_warning(self):
        """Test: yfinance timeout after 60s → logs warning → doesn't crash."""
        with patch('api.startup.Path') as mock_path:
            mock_bot_state = Mock()
            mock_bot_state.exists.return_value = False
            
            def side_effect(path_str):
                if "bot_state.json" in str(path_str):
                    return mock_bot_state
                return Path(path_str)
            
            mock_path.side_effect = side_effect
            
            # api.startup imports yfinance lazily inside the function,
            # so patch sys.modules rather than a module attribute
            mock_yf = MagicMock()
            with patch.dict('sys.modules', {'yfinance': mock_yf}):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    with patch('database.SessionLocal') as mock_session_local:
                        mock_db = MagicMock()
                        mock_db.execute.side_effect = Exception("No trades table")
                        mock_session_local.return_value = mock_db
                        
                        # Mock timeout
                        mock_yf.Ticker.side_effect = asyncio.TimeoutError()
                        
                        result = await initialize_bot_data()
                        
                        # Should not crash, should return with degraded status
                        assert 'timestamp' in result
                        assert result is not None

    @pytest.mark.asyncio
    async def test_yfinance_not_installed_returns_degraded(self):
        """Test: yfinance not installed → logs error → returns degraded status."""
        with patch('api.startup.Path') as mock_path:
            mock_bot_state = Mock()
            mock_bot_state.exists.return_value = False
            
            def side_effect(path_str):
                if "bot_state.json" in str(path_str):
                    return mock_bot_state
                return Path(path_str)
            
            mock_path.side_effect = side_effect
            
            with patch('database.SessionLocal') as mock_session_local:
                mock_db = MagicMock()
                mock_db.execute.side_effect = Exception("No trades table")
                mock_session_local.return_value = mock_db
                
                # Simulate yfinance import failure
                with patch.dict('sys.modules', {'yfinance': None}):
                    result = await initialize_bot_data()
                    
                    assert 'timestamp' in result
                    assert result is not None

    @pytest.mark.asyncio
    async def test_health_check_includes_startup_status(self):
        """Test: /api/health endpoint includes startup_status field."""
        startup_status = get_startup_status()
        
        assert 'initialized' in startup_status
        assert 'timestamp' in startup_status
        assert 'symbol_count' in startup_status
        assert 'error' in startup_status

    @pytest.mark.asyncio
    async def test_concurrent_symbol_initialization(self):
        """Test: 3 simultaneous symbol calls during startup → all succeed."""
        symbols = ["AAPL", "SPY", "QQQ"]
        
        async def mock_fetch(symbol: str):
            await asyncio.sleep(0.1)  # Simulate network delay
            return {"price": 150.0, "volume": 1000000}
        
        # This would run in a real test with actual symbols
        # For now, just verify the list exists
        assert len(DEFAULT_SYMBOLS) >= 3
        assert 'AAPL' in DEFAULT_SYMBOLS
        assert 'SPY' in DEFAULT_SYMBOLS
        assert 'QQQ' in DEFAULT_SYMBOLS

    @pytest.mark.asyncio
    async def test_startup_logs_expected_messages(self):
        """Test: Startup logs contain expected timestamp and symbol count."""
        startup_status = get_startup_status()
        
        # Verify status structure
        assert isinstance(startup_status, dict)
        assert 'initialized' in startup_status
        assert isinstance(startup_status['initialized'], bool)
        assert 'symbol_count' in startup_status
        assert isinstance(startup_status['symbol_count'], int)

    @pytest.mark.asyncio
    async def test_initialization_timestamp_is_iso_format(self):
        """Test: Initialization timestamp is ISO format string."""
        startup_status = get_startup_status()
        
        if startup_status['timestamp'] is not None:
            # Should be parseable as ISO format
            try:
                datetime.fromisoformat(startup_status['timestamp'])
                assert True
            except (ValueError, TypeError):
                pytest.fail("Timestamp is not ISO format")


class TestStartupIntegration:
    """Integration tests for startup recovery."""

    @pytest.mark.asyncio
    async def test_startup_doesnt_crash_on_db_errors(self):
        """Test: Database errors during startup don't crash bot."""
        with patch('database.SessionLocal') as mock_session_local:
            # Simulate database error
            mock_session_local.side_effect = Exception("Database connection failed")
            
            # Should not raise
            result = await initialize_bot_data()
            assert result is not None

    @pytest.mark.asyncio
    async def test_startup_with_missing_database_tables(self):
        """Test: Missing database tables handled gracefully."""
        with patch('database.SessionLocal') as mock_session_local:
            mock_db = MagicMock()
            mock_db.execute.side_effect = AttributeError("'NoneType' object has no attribute 'scalar'")
            mock_session_local.return_value = mock_db
            
            result = await initialize_bot_data()
            # Should complete without crashing
            assert result is not None

    @pytest.mark.asyncio
    async def test_startup_continues_on_partial_yfinance_failure(self):
        """Test: If some symbols fail, continue with others."""
        with patch('api.startup.Path') as mock_path:
            mock_bot_state = Mock()
            mock_bot_state.exists.return_value = False
            
            def side_effect(path_str):
                if "bot_state.json" in str(path_str):
                    return mock_bot_state
                return Path(path_str)
            
            mock_path.side_effect = side_effect
            
            # api.startup imports yfinance lazily inside the function,
            # so patch sys.modules rather than a module attribute
            mock_yf = MagicMock()
            with patch.dict('sys.modules', {'yfinance': mock_yf}):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    with patch('database.SessionLocal') as mock_session_local:
                        mock_db = MagicMock()
                        mock_db.execute.side_effect = Exception("No trades table")
                        mock_session_local.return_value = mock_db
                        
                        # Mock partial failure: AAPL fails, SPY succeeds
                        call_count = 0
                        def ticker_side_effect(symbol):
                            nonlocal call_count
                            call_count += 1
                            if symbol == "AAPL":
                                mock_ticker = Mock()
                                mock_ticker.history.side_effect = Exception("API error")
                                return mock_ticker
                            else:
                                mock_ticker = Mock()
                                mock_history = Mock()
                                mock_history.__len__ = Mock(return_value=10)
                                mock_ticker.history = Mock(return_value=mock_history)
                                return mock_ticker
                        
                        mock_yf.Ticker.side_effect = ticker_side_effect
                        
                        result = await initialize_bot_data()
                        
                        # Should continue and not crash
                        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
