#!/usr/bin/env python3
"""
Test all 5 news sources for Phase 3.2
Verifies: CNBC, Yahoo Finance, MarketWatch, Fox Business, Reuters
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_scrapers.news_monitor import NewsMonitor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_all_sources():
    """Test fetching from all 5 news sources."""
    print("\n" + "=" * 80)
    print("Testing All News Sources (Phase 3.2)")
    print("=" * 80 + "\n")
    
    monitor = NewsMonitor(cache_hours=1, max_articles=20)
    
    sources = [
        ('CNBC', monitor.scrape_cnbc_breaking),
        ('Yahoo Finance', monitor.scrape_yahoo_finance),
        ('MarketWatch', monitor.scrape_marketwatch),
        ('Fox Business', monitor.scrape_fox_business),
        ('Reuters', monitor.scrape_reuters_business)
    ]
    
    results = {}
    total_articles = 0
    
    for source_name, scraper_func in sources:
        print(f"\n[TEST] {source_name}")
        print("-" * 40)
        try:
            articles = scraper_func()
            results[source_name] = {
                'status': '✅ SUCCESS' if articles else '⚠️ NO ARTICLES',
                'count': len(articles),
                'articles': articles
            }
            total_articles += len(articles)
            print(f"Status: {results[source_name]['status']}")
            print(f"Articles: {len(articles)}")
            
            # Show sample headlines
            if articles:
                print(f"\nSample headlines:")
                for article in articles[:3]:
                    category = article['category']
                    title = article['title'][:70]
                    print(f"  [{category}] {title}...")
            
        except Exception as e:
            results[source_name] = {
                'status': '❌ ERROR',
                'count': 0,
                'error': str(e)
            }
            print(f"Status: ❌ ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    success_count = sum(1 for r in results.values() if '✅' in r['status'])
    
    print(f"\nSources tested: {len(sources)}")
    print(f"Successful: {success_count}/{len(sources)}")
    print(f"Total articles: {total_articles}")
    
    print(f"\nBy source:")
    for source_name, result in results.items():
        status = result['status']
        count = result['count']
        print(f"  {source_name}: {status} ({count} articles)")
    
    # Category breakdown
    print(f"\nBy category:")
    by_category = {}
    for result in results.values():
        if 'articles' in result:
            for article in result['articles']:
                cat = article['category']
                by_category[cat] = by_category.get(cat, 0) + 1
    
    for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} articles")
    
    # High-impact events
    print(f"\n⚠️  HIGH-IMPACT EVENTS:")
    important_count = 0
    for result in results.values():
        if 'articles' in result:
            for article in result['articles']:
                if article['category'] in ('IPO', 'M&A', 'Regulatory'):
                    important_count += 1
                    print(f"  [{article['category']}] {article['source']}: {article['title'][:60]}...")
    
    if important_count == 0:
        print("  None detected")
    
    print("\n" + "=" * 80)
    
    if success_count >= 3:
        print("✅ TEST PASSED - At least 3 sources operational")
    else:
        print(f"⚠️  WARNING - Only {success_count}/5 sources working")
    
    print("=" * 80 + "\n")
    
    return results


def test_combined_fetch():
    """Test the combined get_breaking_news method."""
    print("\n" + "=" * 80)
    print("Testing Combined Fetch (get_breaking_news)")
    print("=" * 80 + "\n")
    
    monitor = NewsMonitor(cache_hours=1, max_articles=20)
    
    print("Fetching from all sources...")
    articles = monitor.get_breaking_news(force_refresh=True)
    
    print(f"\nTotal articles: {len(articles)}")
    
    by_source = {}
    for article in articles:
        source = article['source']
        by_source[source] = by_source.get(source, 0) + 1
    
    print(f"\nBy source:")
    for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count} articles")
    
    print("\n" + "=" * 80)
    print("✅ Combined fetch complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Test individual sources
    results = test_all_sources()
    
    # Test combined fetch
    test_combined_fetch()
    
    print("\n🎉 All tests complete!")
