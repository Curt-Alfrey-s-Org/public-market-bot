#!/usr/bin/env python3
"""
Report Generator for market-pie5-bot
Parses logs and generates visual reports and KPI analysis
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np


class LogParser:
    """
    Parse logs and extract KPIs
    """
    
    def __init__(self, log_manager=None, db_path: str = "logs/trading_logs.db"):
        """
        Initialize log parser
        
        Args:
            log_manager: Optional LogManager instance
            db_path: Path to SQLite database
        """
        self.log_manager = log_manager
        self.db_path = Path(db_path)
    
    def calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate from trades"""
        if not trades:
            return 0.0
        
        wins = sum(1 for t in trades if t.get('is_win'))
        return wins / len(trades)
    
    def calculate_roi(self, trades: List[Dict], initial_capital: float) -> float:
        """Calculate return on investment"""
        total_pnl = sum(t.get('pnl', 0) for t in trades if t.get('pnl') is not None)
        return (total_pnl / initial_capital) if initial_capital > 0 else 0.0
    
    def calculate_pnl_trend(self, trades: List[Dict]) -> List[Tuple[str, float]]:
        """
        Calculate cumulative P&L trend over time
        
        Returns:
            List of (timestamp, cumulative_pnl) tuples
        """
        cumulative_pnl = 0
        trend = []
        
        for trade in sorted(trades, key=lambda x: x.get('timestamp', '')):
            pnl = trade.get('pnl', 0)
            if pnl is not None:
                cumulative_pnl += pnl
                trend.append((trade.get('timestamp'), cumulative_pnl))
        
        return trend
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio
        
        Args:
            returns: List of returns
            risk_free_rate: Risk-free rate (default 0)
            
        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate
        
        mean_return = np.mean(excess_returns)
        std_return = np.std(excess_returns)
        
        if std_return == 0:
            return 0.0
        
        return mean_return / std_return
    
    def calculate_max_drawdown(self, pnl_trend: List[Tuple[str, float]]) -> float:
        """
        Calculate maximum drawdown
        
        Args:
            pnl_trend: List of (timestamp, cumulative_pnl) tuples
            
        Returns:
            Maximum drawdown as a percentage
        """
        if not pnl_trend:
            return 0.0
        
        pnl_values = [p[1] for p in pnl_trend]
        peak = pnl_values[0]
        max_dd = 0.0
        
        for value in pnl_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def calculate_rolling_average(self, values: List[float], window: int = 10) -> List[float]:
        """
        Calculate rolling average
        
        Args:
            values: List of values
            window: Window size for rolling average
            
        Returns:
            List of rolling averages
        """
        if len(values) < window:
            return values
        
        result = []
        for i in range(len(values)):
            if i < window - 1:
                result.append(np.mean(values[:i+1]))
            else:
                result.append(np.mean(values[i-window+1:i+1]))
        
        return result
    
    def get_kpis(self, session_id: Optional[str] = None) -> Dict:
        """
        Extract comprehensive KPIs from logs
        
        Args:
            session_id: Optional session ID to filter
            
        Returns:
            Dictionary of KPIs
        """
        # Get trades from database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute("SELECT * FROM trades WHERE session_id = ? ORDER BY timestamp", (session_id,))
        else:
            cursor.execute("SELECT * FROM trades ORDER BY timestamp")
        
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not trades:
            return {
                'error': 'No trades found',
                'total_trades': 0,
                'win_rate': 0.0,
                'roi': 0.0
            }
        
        # Extract KPIs
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.get('is_win'))
        losses = total_trades - wins
        win_rate = self.calculate_win_rate(trades)
        
        total_pnl = sum(t.get('pnl', 0) or 0 for t in trades)
        
        # Calculate returns for Sharpe ratio
        returns = [t.get('pnl_percent', 0) / 100 if t.get('pnl_percent') else 0 for t in trades]
        sharpe_ratio = self.calculate_sharpe_ratio(returns)
        
        # Calculate P&L trend and max drawdown
        pnl_trend = self.calculate_pnl_trend(trades)
        max_drawdown = self.calculate_max_drawdown(pnl_trend)
        
        # Average trade metrics
        avg_win = np.mean([t.get('pnl', 0) for t in trades if t.get('is_win') and t.get('pnl')]) if wins > 0 else 0
        avg_loss = np.mean([t.get('pnl', 0) for t in trades if not t.get('is_win') and t.get('pnl')]) if losses > 0 else 0
        
        # Profit factor
        total_wins = sum(t.get('pnl', 0) for t in trades if t.get('is_win') and t.get('pnl', 0) > 0)
        total_losses = abs(sum(t.get('pnl', 0) for t in trades if not t.get('is_win') and t.get('pnl', 0) < 0))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        kpis = {
            'total_trades': total_trades,
            'winning_trades': wins,
            'losing_trades': losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor,
            'pnl_trend': pnl_trend
        }
        
        return kpis
    
    def compare_strategies(self, session_ids: List[str]) -> Dict:
        """
        Compare performance across multiple sessions/strategies
        
        Args:
            session_ids: List of session IDs to compare
            
        Returns:
            Dictionary with comparison data
        """
        comparison = {}
        
        for session_id in session_ids:
            kpis = self.get_kpis(session_id)
            comparison[session_id] = kpis
        
        return comparison


class ReportGenerator:
    """
    Generate reports and visualizations
    """
    
    def __init__(self, log_parser: LogParser):
        """
        Initialize report generator
        
        Args:
            log_parser: LogParser instance
        """
        self.log_parser = log_parser
    
    def generate_text_report(self, session_id: Optional[str] = None, 
                            output_file: str = "report.txt") -> str:
        """
        Generate a text report
        
        Args:
            session_id: Optional session ID
            output_file: Output file path
            
        Returns:
            Report text
        """
        kpis = self.log_parser.get_kpis(session_id)
        
        if 'error' in kpis:
            return f"Error: {kpis['error']}"
        
        report_lines = [
            "=" * 70,
            "TRADING PERFORMANCE REPORT",
            "=" * 70,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        if session_id:
            report_lines.append(f"Session ID: {session_id}")
            report_lines.append("")
        
        report_lines.extend([
            "KEY PERFORMANCE INDICATORS",
            "-" * 70,
            f"Total Trades:        {kpis['total_trades']}",
            f"Winning Trades:      {kpis['winning_trades']}",
            f"Losing Trades:       {kpis['losing_trades']}",
            f"Win Rate:            {kpis['win_rate']:.1%}",
            "",
            f"Total P&L:           ${kpis['total_pnl']:.2f}",
            f"Average Win:         ${kpis['avg_win']:.2f}",
            f"Average Loss:        ${kpis['avg_loss']:.2f}",
            f"Profit Factor:       {kpis['profit_factor']:.2f}",
            "",
            f"Sharpe Ratio:        {kpis['sharpe_ratio']:.3f}",
            f"Max Drawdown:        {kpis['max_drawdown']:.1%}",
            "=" * 70
        ])
        
        report = "\n".join(report_lines)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(report)
        
        return report
    
    def generate_json_report(self, session_id: Optional[str] = None,
                            output_file: str = "report.json") -> Dict:
        """
        Generate a JSON report
        
        Args:
            session_id: Optional session ID
            output_file: Output file path
            
        Returns:
            Report dictionary
        """
        kpis = self.log_parser.get_kpis(session_id)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'session_id': session_id,
            'kpis': kpis
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def generate_visualization_script(self, session_id: Optional[str] = None,
                                     output_file: str = "visualize.py"):
        """
        Generate a Python script for visualizations using matplotlib
        
        Args:
            session_id: Optional session ID
            output_file: Output file path
        """
        session_id_value = f'"{session_id}"' if session_id else 'None'
        
        script = f'''#!/usr/bin/env python3
"""
Trading Performance Visualization Script
Auto-generated by report_generator.py
"""

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from report_generator import LogParser

# Initialize parser
parser = LogParser()

# Get KPIs
session_id = {session_id_value}
kpis = parser.get_kpis(session_id)

print("Generating visualizations...")

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Trading Performance Analysis', fontsize=16, fontweight='bold')

# Plot 1: P&L Trend
ax1 = axes[0, 0]
pnl_trend = kpis['pnl_trend']
if pnl_trend:
    timestamps = [datetime.fromisoformat(t[0]) for t, _ in pnl_trend]
    pnl_values = [p for _, p in pnl_trend]
    ax1.plot(timestamps, pnl_values, linewidth=2, color='#2E86AB')
    ax1.fill_between(timestamps, pnl_values, alpha=0.3, color='#2E86AB')
    ax1.axhline(y=0, color='gray', linestyle='--', linewidth=1)
    ax1.set_title('Cumulative P&L Over Time')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Cumulative P&L ($)')
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 2: Win Rate Pie Chart
ax2 = axes[0, 1]
wins = kpis['winning_trades']
losses = kpis['losing_trades']
if wins + losses > 0:
    sizes = [wins, losses]
    labels = [f'Wins ({{wins}})', f'Losses ({{losses}})']
    colors = ['#06A77D', '#D8315B']
    ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax2.set_title(f'Win Rate: {{kpis["win_rate"]:.1%}}')

# Plot 3: Performance Metrics Bar Chart
ax3 = axes[1, 0]
metrics = ['Sharpe\\nRatio', 'Profit\\nFactor', 'Max\\nDrawdown']
values = [kpis['sharpe_ratio'], kpis['profit_factor'], kpis['max_drawdown'] * 100]
colors_bar = ['#2E86AB', '#06A77D', '#D8315B']
bars = ax3.bar(metrics, values, color=colors_bar, alpha=0.7)
ax3.set_title('Key Performance Metrics')
ax3.set_ylabel('Value')
ax3.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, value in zip(bars, values):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
             f'{{value:.2f}}', ha='center', va='bottom')

# Plot 4: Trade Statistics
ax4 = axes[1, 1]
ax4.axis('off')
stats_text = f"""
SUMMARY STATISTICS

Total Trades:        {{kpis['total_trades']}}
Win Rate:            {{kpis['win_rate']:.1%}}

Total P&L:           ${{kpis['total_pnl']:.2f}}
Average Win:         ${{kpis['avg_win']:.2f}}
Average Loss:        ${{kpis['avg_loss']:.2f}}

Sharpe Ratio:        {{kpis['sharpe_ratio']:.3f}}
Max Drawdown:        {{kpis['max_drawdown']:.1%}}
Profit Factor:       {{kpis['profit_factor']:.2f}}
"""
ax4.text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
         verticalalignment='center')

plt.tight_layout()
plt.savefig('trading_performance.png', dpi=300, bbox_inches='tight')
print("✓ Visualization saved as 'trading_performance.png'")
plt.show()
'''
        
        with open(output_file, 'w') as f:
            f.write(script)
        
        print(f"✓ Visualization script generated: {output_file}")
        print(f"  Run with: python3 {output_file}")


if __name__ == "__main__":
    import sys
    
    print("Report Generator - Standalone Mode")
    print("=" * 70)
    
    # Check if database exists
    db_path = Path("logs/trading_logs.db")
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run the trading bot first to generate logs.")
        sys.exit(1)
    
    # Create parser and generator
    parser = LogParser(db_path=str(db_path))
    generator = ReportGenerator(parser)
    
    # Generate reports
    print("\nGenerating reports...")
    
    text_report = generator.generate_text_report()
    print("\n" + text_report)
    print("\n✓ Text report saved as 'report.txt'")
    
    json_report = generator.generate_json_report()
    print("✓ JSON report saved as 'report.json'")
    
    generator.generate_visualization_script()
    
    print("\n" + "=" * 70)
    print("Report generation complete!")
    print("\nTo generate visualizations, run:")
    print("  python3 visualize.py")
