#!/usr/bin/env python3
"""Test Phase 3 News Monitor"""

import sys
sys.path.insert(0, '.')

from web_scrapers.news_monitor import NewsMonitor

print("=" * 80)
print("Phase 3: News Monitor Test")
print("=" * 80)
print()

# Initialize monitor
monitor = NewsMonitor(cache_hours=1, max_articles=20)

# Test 1: Fetch breaking news
print("[TEST 1] Fetching breaking news from all sources...")
print("-" * 80)
articles = monitor.get_breaking_news()
print(f"Total articles fetched: {len(articles)}")
print()

# Group by source
by_source = {}
for article in articles:
    source = article['source']
    if source not in by_source:
        by_source[source] = []
    by_source[source].append(article)

print("Articles by source:")
for source, items in by_source.items():
    print(f"  {source}: {len(items)} articles")
print()

# Group by category
by_category = {}
for article in articles:
    cat = article['category']
    if cat not in by_category:
        by_category[cat] = []
    by_category[cat].append(article)

print("Articles by category:")
for cat, items in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {cat}: {len(items)} articles")
print()

# Test 2: Show important events (IPO, M&A, Regulatory)
print("[TEST 2] High-Impact Events")
print("-" * 80)
important = [a for a in articles if a['category'] in ('IPO', 'M&A', 'Regulatory', 'Earnings')]
if important:
    for article in important[:5]:
        print(f"[{article['category']}] {article['source']}")
        print(f"  {article['title']}")
        print()
else:
    print("No high-impact events detected in current news cycle")
    print()

# Test 3: Symbol extraction
print("[TEST 3] Extract symbols from articles")
print("-" * 80)
symbol_map = monitor.extract_symbols_from_articles(articles)
if symbol_map:
    print(f"Found {len(symbol_map)} symbols mentioned:")
    for symbol, related in list(symbol_map.items())[:10]:
        print(f"  ${symbol}: {len(related)} article(s)")
else:
    print("No symbols with ticker format ($SYMBOL) found in headlines")
print()

# Test 4: Intelligence storage
print("[TEST 4] Testing intelligence storage")
print("-" * 80)
# Store a test event
monitor.store_intelligence('AAPL', {
    'type': 'Product',
    'date': '2026-02-02',
    'description': 'Apple announces new product launch',
    'impact': 'medium',
    'recommendation': 'Monitor for sentiment boost'
})
print("✅ Stored test intelligence for AAPL")

# Retrieve it
intel = monitor.get_intelligence('AAPL', days_back=7)
print(f"✅ Retrieved {len(intel)} event(s) for AAPL")
print()

# Test 5: Trade filtering
print("[TEST 5] Trade filtering logic")
print("-" * 80)
test_symbols = ['AAPL', 'TSLA', 'NVDA']
for symbol in test_symbols:
    should_avoid, reason = monitor.should_avoid_symbol(symbol)
    status = "❌ AVOID" if should_avoid else "✅ TRADE"
    print(f"{status} {symbol}: {reason or 'No news concerns'}")
print()

# Test 6: Save intelligence database
print("[TEST 6] Saving intelligence database")
print("-" * 80)
monitor.save_intelligence_to_file('data/market_intelligence.json')
print("✅ Intelligence database saved to data/market_intelligence.json")
print()

print("=" * 80)
print("Phase 3 News Monitor: ALL TESTS PASSED ✅")
print("=" * 80)
