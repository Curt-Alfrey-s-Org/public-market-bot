"""
Messages Routes
Provides stored messages and alerts
"""

from fastapi import APIRouter, HTTPException, Query
from api.utils import get_bot_instance
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("")
async def get_messages(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: Optional[int] = Query(50, description="Limit number of results")
):
    """Get stored messages"""
    bot = get_bot_instance()
    if not bot:
        # Return empty messages when bot is not available instead of 503
        # This allows the UI to show "no messages" instead of an error
        return {
            "messages": [],
            "total": 0
        }
    
    try:
        # Get messages from bot's stored_messages system
        if hasattr(bot, 'stored_messages'):
            messages = bot.get_stored_messages(category=category, limit=limit or 50)
            return {
                "messages": messages,
                "total": len(messages)
            }
        else:
            return {
                "messages": [],
                "total": 0
            }
    except Exception as e:
        logger.error(f"Error getting messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")
