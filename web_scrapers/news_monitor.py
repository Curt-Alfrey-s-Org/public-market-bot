"""
News Event Monitor
Scrapes financial news sites for market-moving events (IPOs, earnings, M&A, etc.)

Sources:
- CNBC Breaking News
- Yahoo Finance
- Fox Business
- MarketWatch
- Bloomberg (if available)

Expected Impact: +10-15% by frontrunning market reactions to major news
"""

import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import re
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)


class NewsMonitor:
    """
    Monitor financial news sites for market-moving events.
    
    Event Types:
    - IPO announcements
    - Earnings beats/misses
    - M&A activity (acquisitions, mergers)
    - FDA approvals (pharma/biotech)
    - Product launches
    - Executive changes
    - Regulatory news
    
    Usage:
        monitor = NewsMonitor(cache_hours=1)
        events = monitor.get_breaking_news()
        if monitor.has_ipo_this_week('RIVN'):
            # Avoid trading during IPO volatility
    """
    
    def __init__(self, cache_hours: int = 1, max_articles: int = 50):
        """
        Initialize news monitor.
        
        Args:
            cache_hours: Hours to cache news data
            max_articles: Maximum articles to fetch per source
        """
        self.cache_hours = cache_hours
        self.max_articles = max_articles
        self.cache: Dict[str, Dict] = {}  # source -> {articles, timestamp}
        self.intelligence_db: Dict[str, List[Dict]] = {}  # symbol -> [events]
        
        # Rotate User-Agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.current_ua_index = 0
        
        logger.info(f"News monitor initialized (cache: {cache_hours}h, max: {max_articles} articles/source)")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with rotated User-Agent."""
        ua = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def scrape_cnbc_breaking(self) -> List[Dict]:
        """
        Scrape CNBC breaking news feed.
        
        Returns:
            List of article dicts with {title, link, timestamp, category}
        """
        try:
            url = "https://www.cnbc.com/world/?region=world"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"CNBC fetch failed: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # CNBC uses various article containers
            for item in soup.find_all('div', class_='Card-titleContainer')[:self.max_articles]:
                try:
                    title_tag = item.find('a')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href', '')
                    
                    # Make absolute URL
                    if link and not link.startswith('http'):
                        link = urljoin('https://www.cnbc.com', link)
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': 'CNBC',
                        'timestamp': datetime.now().isoformat(),
                        'category': self._categorize_article(title)
                    })
                except Exception as e:
                    logger.debug(f"Error parsing CNBC article: {e}")
                    continue
            
            logger.info(f"CNBC: Fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.warning(f"Failed to scrape CNBC: {e}")
            return []
    
    def scrape_yahoo_finance(self) -> List[Dict]:
        """
        Scrape Yahoo Finance latest news.
        
        Returns:
            List of article dicts
        """
        try:
            url = "https://finance.yahoo.com/news/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Yahoo Finance fetch failed: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Yahoo uses various containers
            for item in soup.find_all('h3')[:self.max_articles]:
                try:
                    title_tag = item.find('a')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href', '')
                    
                    if link and not link.startswith('http'):
                        link = urljoin('https://finance.yahoo.com', link)
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': 'Yahoo Finance',
                        'timestamp': datetime.now().isoformat(),
                        'category': self._categorize_article(title)
                    })
                except Exception as e:
                    logger.debug(f"Error parsing Yahoo article: {e}")
                    continue
            
            logger.info(f"Yahoo Finance: Fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.warning(f"Failed to scrape Yahoo Finance: {e}")
            return []
    
    def scrape_marketwatch(self) -> List[Dict]:
        """
        Scrape MarketWatch latest news.
        
        Returns:
            List of article dicts
        """
        try:
            url = "https://www.marketwatch.com/latest-news"
            headers = self._get_headers()
            headers['Referer'] = 'https://www.marketwatch.com/'
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"MarketWatch fetch failed: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            for item in soup.find_all('div', class_='article__content')[:self.max_articles]:
                try:
                    title_tag = item.find('a', class_='link')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href', '')
                    
                    if link and not link.startswith('http'):
                        link = urljoin('https://www.marketwatch.com', link)
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': 'MarketWatch',
                        'timestamp': datetime.now().isoformat(),
                        'category': self._categorize_article(title)
                    })
                except Exception as e:
                    logger.debug(f"Error parsing MarketWatch article: {e}")
                    continue
            
            logger.info(f"MarketWatch: Fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.warning(f"Failed to scrape MarketWatch: {e}")
            return []
    
    def scrape_fox_business(self) -> List[Dict]:
        """
        Scrape Fox Business latest news.
        
        Returns:
            List of article dicts
        """
        try:
            url = "https://www.foxbusiness.com/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Fox Business fetch failed: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Fox Business uses article tags
            for item in soup.find_all('article', class_='article')[:self.max_articles]:
                try:
                    title_tag = item.find('h2', class_='title') or item.find('h3', class_='title')
                    if not title_tag:
                        title_tag = item.find('a')
                    
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link_tag = title_tag if title_tag.name == 'a' else title_tag.find('a', href=True)
                    link = link_tag.get('href', '') if link_tag else ''
                    
                    if link and not link.startswith('http'):
                        link = urljoin('https://www.foxbusiness.com', link)
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': 'Fox Business',
                        'timestamp': datetime.now().isoformat(),
                        'category': self._categorize_article(title)
                    })
                except Exception as e:
                    logger.debug(f"Error parsing Fox Business article: {e}")
                    continue
            
            logger.info(f"Fox Business: Fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.warning(f"Failed to scrape Fox Business: {e}")
            return []
    
    def scrape_reuters_business(self) -> List[Dict]:
        """
        Scrape Reuters business news.
        
        Returns:
            List of article dicts
        """
        try:
            url = "https://www.reuters.com/business/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Reuters fetch failed: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Reuters uses data-testid for story cards
            for item in soup.find_all('div', attrs={'data-testid': 'MediaStoryCard'})[:self.max_articles]:
                try:
                    title_tag = item.find('a', attrs={'data-testid': 'Heading'})
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href', '')
                    
                    if link and not link.startswith('http'):
                        link = urljoin('https://www.reuters.com', link)
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': 'Reuters',
                        'timestamp': datetime.now().isoformat(),
                        'category': self._categorize_article(title)
                    })
                except Exception as e:
                    logger.debug(f"Error parsing Reuters article: {e}")
                    continue
            
            logger.info(f"Reuters: Fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.warning(f"Failed to scrape Reuters: {e}")
            return []
    
    def _categorize_article(self, title: str) -> str:
        """
        Categorize article by keywords in title.
        
        Args:
            title: Article title
        
        Returns:
            Category string
        """
        title_lower = title.lower()
        
        # IPO detection
        if any(word in title_lower for word in ['ipo', 'initial public offering', 'going public', 'debut']):
            return 'IPO'
        
        # Earnings detection
        if any(word in title_lower for word in ['earnings', 'profit', 'revenue', 'eps', 'beats', 'misses']):
            return 'Earnings'
        
        # M&A detection
        if any(word in title_lower for word in ['acquisition', 'merger', 'buyout', 'takeover', 'acquires']):
            return 'M&A'
        
        # FDA/Regulatory
        if any(word in title_lower for word in ['fda', 'approval', 'regulatory', 'cleared']):
            return 'Regulatory'
        
        # Product launches
        if any(word in title_lower for word in ['launch', 'unveils', 'announces', 'new product']):
            return 'Product'
        
        # Executive changes
        if any(word in title_lower for word in ['ceo', 'cfo', 'executive', 'appoints', 'resigns']):
            return 'Executive'
        
        # Market conditions
        if any(word in title_lower for word in ['fed', 'interest rate', 'inflation', 'jobs', 'gdp']):
            return 'Macro'
        
        return 'General'
    
    def get_breaking_news(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all breaking news from all sources.
        
        Args:
            force_refresh: Bypass cache
        
        Returns:
            Combined list of articles from all sources
        """
        # Check cache
        if not force_refresh and 'all_sources' in self.cache:
            cached = self.cache['all_sources']
            cache_age = datetime.now() - cached['timestamp']
            if cache_age < timedelta(hours=self.cache_hours):
                return cached['articles']
        
        # Fetch from all sources
        all_articles = []
        
        all_articles.extend(self.scrape_cnbc_breaking())
        time.sleep(1)  # Rate limiting
        
        all_articles.extend(self.scrape_yahoo_finance())
        time.sleep(1)
        
        all_articles.extend(self.scrape_marketwatch())
        time.sleep(1)
        
        all_articles.extend(self.scrape_fox_business())
        time.sleep(1)
        
        all_articles.extend(self.scrape_reuters_business())
        
        # Cache results
        self.cache['all_sources'] = {
            'articles': all_articles,
            'timestamp': datetime.now()
        }
        
        logger.info(f"Total articles fetched: {len(all_articles)}")
        return all_articles
    
    def extract_symbols_from_articles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract stock symbols mentioned in articles.
        
        Args:
            articles: List of article dicts
        
        Returns:
            Dict mapping symbol -> list of related articles
        """
        symbol_map = {}
        
        # Common ticker pattern: $SYMBOL or (SYMBOL:EXCHANGE)
        ticker_pattern = re.compile(r'\$([A-Z]{1,5})\b|\(([A-Z]{1,5}):[A-Z]+\)')
        
        for article in articles:
            title = article['title']
            matches = ticker_pattern.findall(title)
            
            for match in matches:
                symbol = match[0] or match[1]  # Either $AAPL or (AAPL:NASDAQ)
                
                if symbol not in symbol_map:
                    symbol_map[symbol] = []
                
                symbol_map[symbol].append(article)
        
        return symbol_map
    
    def store_intelligence(self, symbol: str, event: Dict):
        """
        Store long-term market intelligence for symbol.
        
        Args:
            symbol: Stock ticker
            event: Event dict with {type, date, description, impact}
        """
        if symbol not in self.intelligence_db:
            self.intelligence_db[symbol] = []
        
        # Add timestamp if not present
        if 'stored_at' not in event:
            event['stored_at'] = datetime.now().isoformat()
        
        self.intelligence_db[symbol].append(event)
        
        logger.info(f"[INTELLIGENCE] Stored {event.get('type', 'event')} for {symbol}")
    
    def get_intelligence(self, symbol: str, days_back: int = 30) -> List[Dict]:
        """
        Retrieve stored intelligence for symbol.
        
        Args:
            symbol: Stock ticker
            days_back: Days of history to retrieve
        
        Returns:
            List of events for symbol
        """
        if symbol not in self.intelligence_db:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Filter by date
        recent_events = [
            event for event in self.intelligence_db[symbol]
            if datetime.fromisoformat(event['stored_at']) >= cutoff_date
        ]
        
        return recent_events
    
    def has_ipo_this_week(self, symbol: str) -> bool:
        """
        Check if symbol has IPO scheduled this week.
        
        Args:
            symbol: Stock ticker
        
        Returns:
            True if IPO event found in next 7 days
        """
        events = self.get_intelligence(symbol, days_back=7)
        
        for event in events:
            if event.get('type') == 'IPO':
                return True
        
        return False
    
    def should_avoid_symbol(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Check if symbol should be avoided due to news events.
        
        Args:
            symbol: Stock ticker
        
        Returns:
            (should_avoid, reason)
        """
        events = self.get_intelligence(symbol, days_back=7)
        
        # Avoid IPOs (high volatility)
        ipo_events = [e for e in events if e.get('type') == 'IPO']
        if ipo_events:
            return True, f"IPO this week - high volatility expected"
        
        # Caution on M&A (unpredictable)
        ma_events = [e for e in events if e.get('type') == 'M&A']
        if ma_events:
            return True, f"M&A activity - avoid during uncertainty"
        
        # Caution on regulatory news
        reg_events = [e for e in events if e.get('type') == 'Regulatory']
        if reg_events:
            return True, f"Regulatory event - unpredictable outcome"
        
        return False, None
    
    def save_intelligence_to_file(self, filepath: str = 'data/market_intelligence.json'):
        """
        Save intelligence database to JSON file.
        
        Args:
            filepath: Path to save file
        """
        try:
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(self.intelligence_db, f, indent=2)
            
            logger.info(f"Intelligence database saved to {filepath} ({len(self.intelligence_db)} symbols)")
        except Exception as e:
            logger.error(f"Failed to save intelligence database: {e}")
    
    def load_intelligence_from_file(self, filepath: str = 'data/market_intelligence.json'):
        """
        Load intelligence database from JSON file.
        
        Args:
            filepath: Path to load from
        """
        try:
            with open(filepath, 'r') as f:
                self.intelligence_db = json.load(f)
            
            logger.info(f"Intelligence database loaded from {filepath} ({len(self.intelligence_db)} symbols)")
        except FileNotFoundError:
            logger.info(f"No existing intelligence database at {filepath}")
        except Exception as e:
            logger.error(f"Failed to load intelligence database: {e}")
    
    def get_cache_stats(self) -> str:
        """Get cache statistics for daemon status reporting."""
        stats = []
        for source in ['cnbc', 'yahoo', 'marketwatch', 'fox_business', 'reuters']:
            if source in self.cache:
                age_seconds = (datetime.now() - self.cache[source]['timestamp']).total_seconds()
                age_minutes = int(age_seconds / 60)
                count = len(self.cache[source]['articles'])
                stats.append(f"{source}={count} articles ({age_minutes}m old)")
        return ", ".join(stats) if stats else "Empty cache"


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    monitor = NewsMonitor(cache_hours=1, max_articles=20)
    
    print("\n=== Market News Monitor ===\n")
    
    # Fetch breaking news
    articles = monitor.get_breaking_news()
    
    print(f"Total articles: {len(articles)}\n")
    
    # Group by category
    by_category = {}
    for article in articles:
        cat = article['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(article)
    
    print("By Category:")
    for cat, items in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {cat}: {len(items)} articles")
    
    print("\n=== IPO & M&A Alerts ===\n")
    important = [a for a in articles if a['category'] in ('IPO', 'M&A', 'Regulatory')]
    for article in important[:5]:
        print(f"[{article['category']}] {article['source']}")
        print(f"  {article['title']}")
        print(f"  {article['link']}\n")
