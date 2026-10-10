#!/usr/bin/env python3
"""Quick bot status check"""
import sqlite3

conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

print('='*80)
print('Bot Status & Performance')
print('='*80)

# Recent trades
cursor.execute('SELECT timestamp, symbol, action, quantity, price, pnl_usd FROM trades ORDER BY timestamp DESC LIMIT 10')
trades = cursor.fetchall()

print('\nRecent Trades (last 10):')
print('-' * 80)
for t in trades:
    print(f'{t[0]} | {t[1]:5s} | {t[2]:5s} | qty:{t[3]:6.2f} | price:${t[4]:7.2f} | P&L:${t[5]:8.2f}')

# Performance stats
cursor.execute('SELECT COUNT(*), SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END), SUM(pnl_usd) FROM trades WHERE action IN ("SELL", "COVER")')
total, wins, total_pnl = cursor.fetchone()

print('\n' + '='*80)
if total and total > 0:
    win_rate = (wins / total) * 100
    avg_pnl = total_pnl / total
    print(f'Performance Summary:')
    print(f'  Total closed trades: {total}')
    print(f'  Wins: {wins} ({win_rate:.1f}%)')
    print(f'  Total P&L: ${total_pnl:.2f}')
    print(f'  Avg P&L per trade: ${avg_pnl:.2f}')
else:
    print('No closed trades yet')

print('='*80)
conn.close()
