#!/usr/bin/env python3
"""
24/7 News Monitoring Daemon
Continuously scrapes financial news and updates market intelligence database.

Schedule:
- News scraping: Every 1 hour (24/7)
- Intelligence cleanup: Daily at midnight
- Database backup: Daily at 2 AM
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import schedule
import time
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_scrapers.news_monitor import NewsMonitor
from alert_manager import get_alert_manager, alert_news

# Configure logging
LOG_FILE = '/tmp/news_daemon.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
INTELLIGENCE_DB_PATH = 'data/market_intelligence.json'
BACKUP_DIR = 'data/backups'
SCRAPE_INTERVAL_HOURS = 1
CLEANUP_RETENTION_DAYS = 90
MAX_ARTICLES_PER_SOURCE = 50

# Global instances
monitor = None
alert_manager = None


def initialize_monitor():
    """Initialize news monitor and alert system with configuration."""
    global monitor, alert_manager
    try:
        # Initialize news monitor
        monitor = NewsMonitor(cache_hours=1, max_articles=MAX_ARTICLES_PER_SOURCE)
        
        # Initialize alert system
        alert_manager = get_alert_manager(enabled=True)
        logger.info("Alert system initialized for popup notifications")
        # Load existing intelligence database
        if os.path.exists(INTELLIGENCE_DB_PATH):
            monitor.load_intelligence_from_file(INTELLIGENCE_DB_PATH)
            logger.info(f"Loaded existing intelligence database: {len(monitor.intelligence_db)} symbols")
        else:
            logger.info("Starting with empty intelligence database")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize news monitor: {e}")
        return False


def scrape_and_store():
    """
    Main scraping task: Fetch news and update intelligence database.
    Runs every hour.
    """
    logger.info("=" * 80)
    logger.info("Starting news scraping cycle")
    logger.info("=" * 80)
    
    try:
        # Fetch breaking news from all sources
        articles = monitor.get_breaking_news(force_refresh=True)
        logger.info(f"Fetched {len(articles)} total articles")
        
        # Group by source
        by_source = {}
        for article in articles:
            source = article['source']
            by_source[source] = by_source.get(source, 0) + 1
        
        for source, count in by_source.items():
            logger.info(f"  {source}: {count} articles")
        
        # Group by category
        by_category = {}
        for article in articles:
            cat = article['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        logger.info(f"By category: {dict(by_category)}")
        
        # Extract symbols mentioned in articles
        symbol_map = monitor.extract_symbols_from_articles(articles)
        logger.info(f"Found {len(symbol_map)} symbols mentioned in articles")
        
        # Store intelligence for high-impact events
        events_stored = 0
        for symbol, related_articles in symbol_map.items():
            for article in related_articles:
                # Only store high-impact events
                if article['category'] in ('IPO', 'M&A', 'Regulatory', 'Earnings', 'Executive'):
                    monitor.store_intelligence(symbol, {
                        'type': article['category'],
                        'date': article['timestamp'],
                        'description': article['title'],
                        'source': article['source'],
                        'link': article['link'],
                        'impact': 'high' if article['category'] in ('IPO', 'M&A', 'Regulatory') else 'medium',
                        'recommendation': get_recommendation(article['category'])
                    })
                    events_stored += 1
        
        logger.info(f"Stored {events_stored} intelligence events")
        
        # Save database to disk
        monitor.save_intelligence_to_file(INTELLIGENCE_DB_PATH)
        logger.info(f"Intelligence database saved: {len(monitor.intelligence_db)} symbols, {get_total_events()} events")
        
        # Log and alert high-impact events
        important = [a for a in articles if a['category'] in ('IPO', 'M&A', 'Regulatory')]
        if important:
            logger.warning(f"⚠️  {len(important)} HIGH-IMPACT EVENTS detected:")
            for article in important[:5]:
                logger.warning(f"  [{article['category']}] {article['title'][:80]}...")
                
                # Send desktop notification for high-impact events
                try:
                    if alert_manager:
                        # Extract symbol if mentioned in title
                        title_upper = article['title'].upper()
                        symbol = None
                        # Simple symbol extraction (look for $SYMBOL or common patterns)
                        import re
                        match = re.search(r'\$([A-Z]{1,5})\b', title_upper)
                        if match:
                            symbol = match.group(1)
                        
                        if symbol:
                            alert_news(
                                symbol=symbol,
                                event_type=article['category'],
                                description=article['title'][:150],
                                impact='high'
                            )
                        else:
                            # Alert without symbol
                            alert_manager.send_notification(
                                title=f"🚨 {article['category']} Event",
                                message=article['title'][:150],
                                duration=12
                            )
                except Exception as e:
                    logger.debug(f"Failed to send alert: {e}")
        
        logger.info("Scraping cycle complete ✅")
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)


def get_recommendation(event_type: str) -> str:
    """Get trading recommendation based on event type."""
    recommendations = {
        'IPO': 'Avoid trading for 5-7 days post-IPO (high volatility)',
        'M&A': 'Avoid during negotiation period (uncertainty)',
        'Regulatory': 'Avoid before decision (binary outcome risk)',
        'Earnings': 'Use earnings calendar filter (already deployed)',
        'Executive': 'Monitor during transition period (30-90 days)',
        'Product': 'Monitor for sentiment boost',
        'Macro': 'Use Phase 2.1 macro calendar'
    }
    return recommendations.get(event_type, 'Monitor for impact')


def get_total_events() -> int:
    """Count total events in intelligence database."""
    total = 0
    for symbol, events in monitor.intelligence_db.items():
        total += len(events)
    return total


def cleanup_expired_intelligence():
    """
    Clean up old intelligence events.
    Runs daily at midnight.
    """
    logger.info("=" * 80)
    logger.info("Starting intelligence cleanup")
    logger.info("=" * 80)
    
    try:
        cutoff_date = datetime.now() - timedelta(days=CLEANUP_RETENTION_DAYS)
        logger.info(f"Removing events older than {CLEANUP_RETENTION_DAYS} days (before {cutoff_date.date()})")
        
        removed_count = 0
        for symbol in list(monitor.intelligence_db.keys()):
            events = monitor.intelligence_db[symbol]
            
            # Keep only recent events
            recent_events = [
                e for e in events
                if datetime.fromisoformat(e['stored_at']) >= cutoff_date
            ]
            
            removed = len(events) - len(recent_events)
            if removed > 0:
                logger.info(f"  {symbol}: Removed {removed} old event(s)")
                removed_count += removed
            
            if recent_events:
                monitor.intelligence_db[symbol] = recent_events
            else:
                # Remove symbol entirely if no events left
                del monitor.intelligence_db[symbol]
        
        # Save cleaned database
        monitor.save_intelligence_to_file(INTELLIGENCE_DB_PATH)
        logger.info(f"Cleanup complete: Removed {removed_count} old events")
        logger.info(f"Current database: {len(monitor.intelligence_db)} symbols, {get_total_events()} events")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)


def backup_intelligence_database():
    """
    Create daily backup of intelligence database.
    Runs daily at 2 AM.
    """
    logger.info("=" * 80)
    logger.info("Creating intelligence database backup")
    logger.info("=" * 80)
    
    try:
        # Create backup directory
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Backup filename with date
        backup_filename = f"market_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Copy current database
        if os.path.exists(INTELLIGENCE_DB_PATH):
            with open(INTELLIGENCE_DB_PATH, 'r') as f:
                data = json.load(f)
            
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Get file size
            size_bytes = os.path.getsize(backup_path)
            size_kb = size_bytes / 1024
            
            logger.info(f"Backup created: {backup_path} ({size_kb:.1f} KB)")
            
            # Clean up old backups (keep last 7 days)
            cleanup_old_backups(days_to_keep=7)
        else:
            logger.warning(f"No database file to backup at {INTELLIGENCE_DB_PATH}")
        
    except Exception as e:
        logger.error(f"Error during backup: {e}", exc_info=True)


def cleanup_old_backups(days_to_keep: int = 7):
    """Remove backups older than N days."""
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed = 0
        
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('market_intelligence_') and filename.endswith('.json'):
                filepath = os.path.join(BACKUP_DIR, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    removed += 1
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old backup(s)")
    
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")


def print_status():
    """Print current daemon status."""
    logger.info("=" * 80)
    logger.info("News Monitoring Daemon - Status Report")
    logger.info("=" * 80)
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Intelligence Database: {len(monitor.intelligence_db)} symbols, {get_total_events()} events")
    logger.info(f"Cache Stats: {monitor.get_cache_stats()}")
    logger.info(f"Next scrape: {schedule.next_run()}")
    logger.info("=" * 80)


def main():
    """Main daemon loop."""
    logger.info("=" * 80)
    logger.info("Market Bot News Monitoring Daemon Starting")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  Scrape Interval: Every {SCRAPE_INTERVAL_HOURS} hour(s)")
    logger.info(f"  Intelligence DB: {INTELLIGENCE_DB_PATH}")
    logger.info(f"  Retention: {CLEANUP_RETENTION_DAYS} days")
    logger.info(f"  Max Articles/Source: {MAX_ARTICLES_PER_SOURCE}")
    logger.info(f"  Log File: {LOG_FILE}")
    logger.info("=" * 80)
    
    # Initialize monitor
    if not initialize_monitor():
        logger.error("Failed to initialize monitor. Exiting.")
        return 1
    
    # Schedule tasks
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(scrape_and_store)
    schedule.every().day.at("00:00").do(cleanup_expired_intelligence)
    schedule.every().day.at("02:00").do(backup_intelligence_database)
    schedule.every(6).hours.do(print_status)
    
    logger.info("Scheduled tasks:")
    logger.info(f"  - News scraping: Every {SCRAPE_INTERVAL_HOURS} hour(s)")
    logger.info(f"  - Cleanup: Daily at 00:00")
    logger.info(f"  - Backup: Daily at 02:00")
    logger.info(f"  - Status: Every 6 hours")
    logger.info("=" * 80)
    
    # Run initial scrape immediately
    logger.info("Running initial scraping cycle...")
    scrape_and_store()
    
    # Main loop
    logger.info("Entering main loop (Press Ctrl+C to stop)")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        return 1
    finally:
        logger.info("News monitoring daemon stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
