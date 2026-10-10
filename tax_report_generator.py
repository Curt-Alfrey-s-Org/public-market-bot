#!/usr/bin/env python3
"""
Tax Report Generator for market-pie5-bot
Generates IRS Form 8949 compatible reports for capital gains/losses
Suitable for CPA review and tax filing purposes
"""

import csv
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TaxReportGenerator:
    """
    Generate tax-compliant reports for trading activity
    Supports IRS Form 8949 and Schedule D requirements
    """
    
    def __init__(self, db_path: str = "logs/trading_logs.db"):
        """
        Initialize tax report generator
        
        Args:
            db_path: Path to SQLite trading logs database
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Trading logs database not found: {db_path}")
    
    def get_trades_for_tax_year(self, tax_year: int) -> List[Dict]:
        """
        Get all completed trades for a specific tax year
        A completed trade is a SELL transaction (closed position)
        
        Note: For accurate holding period calculation, the trade should include
        an 'acquisition_timestamp' field. If not available, we use the SELL
        timestamp as a fallback (resulting in 0-day holding period).
        
        Args:
            tax_year: Tax year (e.g., 2024)
            
        Returns:
            List of completed trade dictionaries with tax information
        """
        start_date = f"{tax_year}-01-01T00:00:00"
        end_date = f"{tax_year}-12-31T23:59:59"
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all SELL trades for the tax year (SELL trades indicate closed positions)
        cursor.execute("""
            SELECT * FROM trades 
            WHERE timestamp >= ? AND timestamp <= ?
            AND action = 'SELL'
            ORDER BY timestamp
        """, (start_date, end_date))
        
        sell_trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # For each SELL trade, try to find corresponding BUY trade to get acquisition date
        for trade in sell_trades:
            # Check if trade already has acquisition timestamp in metadata
            if 'acquisition_timestamp' not in trade:
                # Try to find it in metadata field
                try:
                    metadata = json.loads(trade.get('metadata', '{}'))
                    if 'acquisition_timestamp' in metadata:
                        trade['acquisition_timestamp'] = metadata['acquisition_timestamp']
                except:
                    pass
            
            # If still not found, search for matching BUY trade
            if 'acquisition_timestamp' not in trade:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Find most recent BUY for this symbol before the SELL
                cursor.execute("""
                    SELECT timestamp FROM trades
                    WHERE symbol = ?
                    AND action = 'BUY'
                    AND timestamp < ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (trade['symbol'], trade['timestamp']))
                
                buy_trade = cursor.fetchone()
                conn.close()
                
                if buy_trade:
                    trade['acquisition_timestamp'] = buy_trade['timestamp']
                else:
                    # Fallback: Use SELL timestamp (results in 0-day holding period)
                    # This will classify as short-term
                    trade['acquisition_timestamp'] = trade['timestamp']
                    logger.warning(f"No BUY trade found for {trade['symbol']} - using SELL date as acquisition date")
        
        return sell_trades
    
    def classify_holding_period(self, acquisition_date: str, sale_date: str) -> str:
        """
        Classify trade as short-term or long-term based on holding period
        IRS rules: >365 days = long-term, <=365 days = short-term
        
        Args:
            acquisition_date: Date position was opened (ISO format)
            sale_date: Date position was closed (ISO format)
            
        Returns:
            'short-term' or 'long-term'
        """
        try:
            acq_dt = datetime.fromisoformat(acquisition_date.replace('Z', '+00:00'))
            sale_dt = datetime.fromisoformat(sale_date.replace('Z', '+00:00'))
            
            days_held = (sale_dt - acq_dt).days
            
            return 'long-term' if days_held > 365 else 'short-term'
        except Exception as e:
            logger.warning(f"Error classifying holding period: {e}")
            return 'short-term'  # Default to short-term if calculation fails
    
    def detect_wash_sales(self, trades: List[Dict]) -> List[Dict]:
        """
        Detect potential wash sales (selling at a loss and repurchasing within 30 days)
        IRS Wash Sale Rule: Can't claim loss if same/substantially identical security
        is purchased within 30 days before or after the sale
        
        Args:
            trades: List of all trades (both BUY and SELL)
            
        Returns:
            List of trades with wash_sale flag added
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all trades for wash sale detection (need both BUY and SELL)
        cursor.execute("""
            SELECT * FROM trades 
            ORDER BY timestamp
        """)
        
        all_trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Group trades by symbol
        trades_by_symbol = defaultdict(list)
        for trade in all_trades:
            trades_by_symbol[trade['symbol']].append(trade)
        
        # Check each SELL trade for wash sales
        for trade in trades:
            trade['wash_sale'] = False
            
            # Only check losing trades
            if trade.get('pnl', 0) >= 0:
                continue
            
            symbol = trade['symbol']
            sale_date = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
            
            # Check for purchases within 30 days before or after
            for other_trade in trades_by_symbol[symbol]:
                if other_trade['action'] != 'BUY':
                    continue
                
                purchase_date = datetime.fromisoformat(other_trade['timestamp'].replace('Z', '+00:00'))
                days_diff = abs((purchase_date - sale_date).days)
                
                # Wash sale if purchased within 30 days (before or after)
                if days_diff <= 30 and purchase_date != sale_date:
                    trade['wash_sale'] = True
                    trade['wash_sale_details'] = {
                        'repurchase_date': other_trade['timestamp'],
                        'days_difference': days_diff
                    }
                    break
        
        return trades
    
    def generate_form_8949_csv(self, tax_year: int, output_file: str = None) -> str:
        """
        Generate IRS Form 8949 compatible CSV report
        Form 8949: Sales and Other Dispositions of Capital Assets
        
        Args:
            tax_year: Tax year for the report
            output_file: Optional custom filename
            
        Returns:
            Path to generated CSV file
        """
        if output_file is None:
            output_file = f'form_8949_tax_year_{tax_year}.csv'
        
        trades = self.get_trades_for_tax_year(tax_year)
        trades = self.detect_wash_sales(trades)
        
        # Sort by holding period
        short_term = []
        long_term = []
        
        for trade in trades:
            # Use acquisition_timestamp if available, otherwise fall back to timestamp
            acquisition_date = trade.get('acquisition_timestamp', trade['timestamp'])
            sale_date = trade['timestamp']
            
            holding_period = self.classify_holding_period(acquisition_date, sale_date)
            
            if holding_period == 'short-term':
                short_term.append(trade)
            else:
                long_term.append(trade)
        
        # Write to CSV in Form 8949 format
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header information
            writer.writerow(['IRS Form 8949 - Sales and Other Dispositions of Capital Assets'])
            writer.writerow([f'Tax Year: {tax_year}'])
            writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow([])
            
            # Part I: Short-Term Capital Gains and Losses
            writer.writerow(['PART I: SHORT-TERM CAPITAL GAINS AND LOSSES'])
            writer.writerow(['Assets held one year or less'])
            writer.writerow([])
            
            # Column headers matching Form 8949
            writer.writerow([
                '(a) Description of property',
                '(b) Date acquired',
                '(c) Date sold',
                '(d) Proceeds (sales price)',
                '(e) Cost (or other basis)',
                '(f) Adjustment code',
                '(g) Adjustment amount',
                '(h) Gain or (loss)',
                'Wash Sale?'
            ])
            
            short_term_total_proceeds = 0
            short_term_total_cost = 0
            short_term_total_gain = 0
            
            for trade in short_term:
                description = f"{trade['symbol']} - {trade.get('quantity', 0)} shares"
                date_acquired = trade.get('acquisition_timestamp', trade['timestamp'])[:10]
                date_sold = trade['timestamp'][:10]
                proceeds = trade.get('exit_price', 0) * trade.get('quantity', 0)
                cost_basis = trade.get('entry_price', 0) * trade.get('quantity', 0)
                adjustment_code = 'W' if trade.get('wash_sale', False) else ''
                adjustment_amount = 0  # Wash sale adjustment would go here
                gain_loss = trade.get('pnl', 0)
                wash_sale_flag = 'YES' if trade.get('wash_sale', False) else 'NO'
                
                writer.writerow([
                    description,
                    date_acquired,
                    date_sold,
                    f"${proceeds:.2f}",
                    f"${cost_basis:.2f}",
                    adjustment_code,
                    f"${adjustment_amount:.2f}",
                    f"${gain_loss:.2f}",
                    wash_sale_flag
                ])
                
                short_term_total_proceeds += proceeds
                short_term_total_cost += cost_basis
                short_term_total_gain += gain_loss
            
            writer.writerow([])
            writer.writerow([
                'TOTALS',
                '',
                '',
                f"${short_term_total_proceeds:.2f}",
                f"${short_term_total_cost:.2f}",
                '',
                '',
                f"${short_term_total_gain:.2f}",
                ''
            ])
            writer.writerow([])
            writer.writerow([])
            
            # Part II: Long-Term Capital Gains and Losses
            writer.writerow(['PART II: LONG-TERM CAPITAL GAINS AND LOSSES'])
            writer.writerow(['Assets held more than one year'])
            writer.writerow([])
            
            writer.writerow([
                '(a) Description of property',
                '(b) Date acquired',
                '(c) Date sold',
                '(d) Proceeds (sales price)',
                '(e) Cost (or other basis)',
                '(f) Adjustment code',
                '(g) Adjustment amount',
                '(h) Gain or (loss)',
                'Wash Sale?'
            ])
            
            long_term_total_proceeds = 0
            long_term_total_cost = 0
            long_term_total_gain = 0
            
            for trade in long_term:
                description = f"{trade['symbol']} - {trade.get('quantity', 0)} shares"
                date_acquired = trade.get('acquisition_timestamp', trade['timestamp'])[:10]
                date_sold = trade['timestamp'][:10]
                proceeds = trade.get('exit_price', 0) * trade.get('quantity', 0)
                cost_basis = trade.get('entry_price', 0) * trade.get('quantity', 0)
                adjustment_code = 'W' if trade.get('wash_sale', False) else ''
                adjustment_amount = 0
                gain_loss = trade.get('pnl', 0)
                wash_sale_flag = 'YES' if trade.get('wash_sale', False) else 'NO'
                
                writer.writerow([
                    description,
                    date_acquired,
                    date_sold,
                    f"${proceeds:.2f}",
                    f"${cost_basis:.2f}",
                    adjustment_code,
                    f"${adjustment_amount:.2f}",
                    f"${gain_loss:.2f}",
                    wash_sale_flag
                ])
                
                long_term_total_proceeds += proceeds
                long_term_total_cost += cost_basis
                long_term_total_gain += gain_loss
            
            writer.writerow([])
            writer.writerow([
                'TOTALS',
                '',
                '',
                f"${long_term_total_proceeds:.2f}",
                f"${long_term_total_cost:.2f}",
                '',
                '',
                f"${long_term_total_gain:.2f}",
                ''
            ])
            writer.writerow([])
            writer.writerow([])
            
            # Summary for Schedule D
            writer.writerow(['SUMMARY FOR SCHEDULE D'])
            writer.writerow(['Short-term total (Part I):', f"${short_term_total_gain:.2f}"])
            writer.writerow(['Long-term total (Part II):', f"${long_term_total_gain:.2f}"])
            writer.writerow(['Net capital gain or (loss):', f"${short_term_total_gain + long_term_total_gain:.2f}"])
        
        logger.info(f"Generated Form 8949 CSV: {output_file}")
        print(f"\n✓ Generated IRS Form 8949 CSV: {output_file}")
        print(f"  Short-term trades: {len(short_term)}")
        print(f"  Long-term trades: {len(long_term)}")
        print(f"  Total capital gain/loss: ${short_term_total_gain + long_term_total_gain:.2f}")
        
        return output_file
    
    def generate_tax_summary_json(self, tax_year: int, output_file: str = None) -> str:
        """
        Generate comprehensive tax summary in JSON format
        
        Args:
            tax_year: Tax year for the report
            output_file: Optional custom filename
            
        Returns:
            Path to generated JSON file
        """
        if output_file is None:
            output_file = f'tax_summary_{tax_year}.json'
        
        trades = self.get_trades_for_tax_year(tax_year)
        trades = self.detect_wash_sales(trades)
        
        # Calculate statistics
        short_term_trades = []
        long_term_trades = []
        wash_sales = []
        
        for trade in trades:
            acquisition_date = trade.get('acquisition_timestamp', trade['timestamp'])
            sale_date = trade['timestamp']
            holding_period = self.classify_holding_period(acquisition_date, sale_date)
            
            trade_info = {
                'symbol': trade['symbol'],
                'quantity': trade.get('quantity', 0),
                'date_acquired': acquisition_date[:10],
                'date_sold': sale_date[:10],
                'entry_price': trade.get('entry_price', 0),
                'exit_price': trade.get('exit_price', 0),
                'proceeds': trade.get('exit_price', 0) * trade.get('quantity', 0),
                'cost_basis': trade.get('entry_price', 0) * trade.get('quantity', 0),
                'gain_loss': trade.get('pnl', 0),
                'holding_period': holding_period,
                'wash_sale': trade.get('wash_sale', False)
            }
            
            if holding_period == 'short-term':
                short_term_trades.append(trade_info)
            else:
                long_term_trades.append(trade_info)
            
            if trade.get('wash_sale', False):
                wash_sales.append(trade_info)
        
        # Calculate totals
        short_term_gain = sum(t['gain_loss'] for t in short_term_trades)
        long_term_gain = sum(t['gain_loss'] for t in long_term_trades)
        total_gain = short_term_gain + long_term_gain
        
        summary = {
            'tax_year': tax_year,
            'generated_date': datetime.now().isoformat(),
            'summary': {
                'total_trades': len(trades),
                'short_term_trades': len(short_term_trades),
                'long_term_trades': len(long_term_trades),
                'wash_sales_detected': len(wash_sales),
                'short_term_gain_loss': short_term_gain,
                'long_term_gain_loss': long_term_gain,
                'net_capital_gain_loss': total_gain
            },
            'short_term_trades': short_term_trades,
            'long_term_trades': long_term_trades,
            'wash_sales': wash_sales,
            'notes': [
                'This report is for informational purposes only.',
                'Please consult with a qualified tax professional for tax advice.',
                'Wash sale rules may affect your ability to claim losses.',
                'Form 8949 must be filed with your tax return to report these transactions.'
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Generated tax summary JSON: {output_file}")
        print(f"\n✓ Generated tax summary JSON: {output_file}")
        
        return output_file
    
    def generate_cpa_report(self, tax_year: int, output_file: str = None) -> str:
        """
        Generate comprehensive text report for CPA review
        
        Args:
            tax_year: Tax year for the report
            output_file: Optional custom filename
            
        Returns:
            Path to generated report file
        """
        if output_file is None:
            output_file = f'cpa_report_{tax_year}.txt'
        
        trades = self.get_trades_for_tax_year(tax_year)
        trades = self.detect_wash_sales(trades)
        
        # Classify trades
        short_term_trades = []
        long_term_trades = []
        
        for trade in trades:
            acquisition_date = trade.get('acquisition_timestamp', trade['timestamp'])
            sale_date = trade['timestamp']
            holding_period = self.classify_holding_period(acquisition_date, sale_date)
            
            if holding_period == 'short-term':
                short_term_trades.append(trade)
            else:
                long_term_trades.append(trade)
        
        # Generate report
        lines = []
        lines.append("=" * 80)
        lines.append("TRADING TAX REPORT FOR CPA REVIEW")
        lines.append("=" * 80)
        lines.append(f"Tax Year: {tax_year}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("IMPORTANT: This report is generated from trading bot logs.")
        lines.append("Please verify all information with brokerage statements (Form 1099-B).")
        lines.append("")
        
        # Summary section
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Completed Trades: {len(trades)}")
        lines.append(f"Short-Term Trades (≤365 days): {len(short_term_trades)}")
        lines.append(f"Long-Term Trades (>365 days): {len(long_term_trades)}")
        
        wash_sales = [t for t in trades if t.get('wash_sale', False)]
        lines.append(f"Potential Wash Sales Detected: {len(wash_sales)}")
        lines.append("")
        
        # Calculate totals
        short_term_gain = sum(t.get('pnl', 0) for t in short_term_trades)
        long_term_gain = sum(t.get('pnl', 0) for t in long_term_trades)
        total_gain = short_term_gain + long_term_gain
        
        lines.append(f"Short-Term Capital Gain/(Loss): ${short_term_gain:,.2f}")
        lines.append(f"Long-Term Capital Gain/(Loss): ${long_term_gain:,.2f}")
        lines.append(f"Net Capital Gain/(Loss): ${total_gain:,.2f}")
        lines.append("")
        lines.append("")
        
        # Short-term trades detail
        if short_term_trades:
            lines.append("SHORT-TERM CAPITAL GAINS AND LOSSES (≤365 days)")
            lines.append("-" * 80)
            lines.append(f"{'Symbol':<10} {'Qty':<8} {'Acquired':<12} {'Sold':<12} {'Cost Basis':<15} {'Proceeds':<15} {'Gain/Loss':<15} {'Wash Sale'}")
            lines.append("-" * 80)
            
            for trade in short_term_trades:
                symbol = trade['symbol']
                quantity = trade.get('quantity', 0)
                acquired = trade.get('acquisition_timestamp', trade['timestamp'])[:10]
                sold = trade['timestamp'][:10]
                cost_basis = trade.get('entry_price', 0) * quantity
                proceeds = trade.get('exit_price', 0) * quantity
                gain_loss = trade.get('pnl', 0)
                wash_flag = 'YES' if trade.get('wash_sale', False) else 'NO'
                
                lines.append(f"{symbol:<10} {quantity:<8.2f} {acquired:<12} {sold:<12} ${cost_basis:<14,.2f} ${proceeds:<14,.2f} ${gain_loss:<14,.2f} {wash_flag}")
            
            lines.append("-" * 80)
            lines.append(f"{'TOTAL':<10} {'':<8} {'':<12} {'':<12} {'':<15} {'':<15} ${short_term_gain:<14,.2f}")
            lines.append("")
            lines.append("")
        
        # Long-term trades detail
        if long_term_trades:
            lines.append("LONG-TERM CAPITAL GAINS AND LOSSES (>365 days)")
            lines.append("-" * 80)
            lines.append(f"{'Symbol':<10} {'Qty':<8} {'Acquired':<12} {'Sold':<12} {'Cost Basis':<15} {'Proceeds':<15} {'Gain/Loss':<15} {'Wash Sale'}")
            lines.append("-" * 80)
            
            for trade in long_term_trades:
                symbol = trade['symbol']
                quantity = trade.get('quantity', 0)
                acquired = trade.get('acquisition_timestamp', trade['timestamp'])[:10]
                sold = trade['timestamp'][:10]
                cost_basis = trade.get('entry_price', 0) * quantity
                proceeds = trade.get('exit_price', 0) * quantity
                gain_loss = trade.get('pnl', 0)
                wash_flag = 'YES' if trade.get('wash_sale', False) else 'NO'
                
                lines.append(f"{symbol:<10} {quantity:<8.2f} {acquired:<12} {sold:<12} ${cost_basis:<14,.2f} ${proceeds:<14,.2f} ${gain_loss:<14,.2f} {wash_flag}")
            
            lines.append("-" * 80)
            lines.append(f"{'TOTAL':<10} {'':<8} {'':<12} {'':<12} {'':<15} {'':<15} ${long_term_gain:<14,.2f}")
            lines.append("")
            lines.append("")
        
        # Wash sales detail
        if wash_sales:
            lines.append("POTENTIAL WASH SALES (30-DAY RULE)")
            lines.append("-" * 80)
            lines.append("NOTE: These transactions may be subject to IRS wash sale rules.")
            lines.append("Loss deductions may be disallowed or deferred.")
            lines.append("")
            
            for trade in wash_sales:
                lines.append(f"Symbol: {trade['symbol']}")
                lines.append(f"  Sale Date: {trade['timestamp'][:10]}")
                lines.append(f"  Loss: ${trade.get('pnl', 0):,.2f}")
                if 'wash_sale_details' in trade:
                    lines.append(f"  Repurchase Date: {trade['wash_sale_details']['repurchase_date'][:10]}")
                    lines.append(f"  Days Difference: {trade['wash_sale_details']['days_difference']}")
                lines.append("")
        
        lines.append("")
        lines.append("NOTES AND DISCLAIMERS")
        lines.append("-" * 80)
        lines.append("1. This report is generated from trading bot logs and should be verified")
        lines.append("   against official brokerage statements (Form 1099-B).")
        lines.append("2. Wash sale detection is automated but should be manually reviewed.")
        lines.append("3. All dates are in ISO format (YYYY-MM-DD).")
        lines.append("4. Cost basis includes commission/fees if captured in trade logs.")
        lines.append("5. Consult with a qualified tax professional for filing requirements.")
        lines.append("")
        lines.append("FILES GENERATED:")
        lines.append(f"  - Form 8949 CSV: form_8949_tax_year_{tax_year}.csv")
        lines.append(f"  - Tax Summary JSON: tax_summary_{tax_year}.json")
        lines.append(f"  - CPA Report: {output_file}")
        lines.append("=" * 80)
        
        report = "\n".join(lines)
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Generated CPA report: {output_file}")
        print(f"\n✓ Generated CPA report: {output_file}")
        print(report)
        
        return output_file
    
    def generate_all_reports(self, tax_year: int) -> Dict[str, str]:
        """
        Generate all tax reports for a given tax year
        
        Args:
            tax_year: Tax year for reports
            
        Returns:
            Dictionary mapping report type to filename
        """
        print(f"\nGenerating all tax reports for tax year {tax_year}...")
        print("=" * 80)
        
        reports = {}
        
        try:
            reports['form_8949_csv'] = self.generate_form_8949_csv(tax_year)
            reports['tax_summary_json'] = self.generate_tax_summary_json(tax_year)
            reports['cpa_report'] = self.generate_cpa_report(tax_year)
            
            print(f"\n✓ All tax reports generated successfully!")
            print(f"\nGenerated files:")
            for report_type, filename in reports.items():
                print(f"  - {filename}")
            
        except Exception as e:
            logger.error(f"Error generating tax reports: {e}")
            print(f"\n✗ Error generating tax reports: {e}")
            raise
        
        return reports


if __name__ == "__main__":
    import sys
    
    print("Tax Report Generator")
    print("=" * 80)
    
    # Check if database exists
    db_path = Path("logs/trading_logs.db")
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run the trading bot first to generate logs.")
        sys.exit(1)
    
    # Get tax year from command line or use current year
    tax_year = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.now().year
    
    print(f"Generating tax reports for year {tax_year}...")
    print()
    
    # Generate all reports
    generator = TaxReportGenerator(db_path=str(db_path))
    reports = generator.generate_all_reports(tax_year)
    
    print("\n" + "=" * 80)
    print("Tax report generation complete!")
    print("\nNext steps:")
    print("1. Review all generated files for accuracy")
    print("2. Compare with brokerage statements (Form 1099-B)")
    print("3. Provide files to your CPA for tax preparation")
    print("4. Keep copies for your records (7 years recommended)")
