"""
Bot Wrapper Module
Provides interface between FastAPI and TradingBot class
"""

from api.utils import set_bot_instance, get_bot_instance
import logging

logger = logging.getLogger(__name__)

def initialize_bot(bot):
    """
    Initialize bot instance for API
    
    Args:
        bot: TradingBot instance
    """
    set_bot_instance(bot)
    logger.info("Bot instance initialized for API")

def get_bot():
    """Get the bot instance"""
    return get_bot_instance()
