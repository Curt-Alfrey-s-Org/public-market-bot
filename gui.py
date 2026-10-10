#!/usr/bin/env python3
"""
Market Pie5 Bot - GUI Application
Lightweight Tkinter GUI for Raspberry Pi 5
"""

import sys
import os

# Check if tkinter is available before importing
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
    TKINTER_AVAILABLE = True
except ImportError as exc:
    TKINTER_AVAILABLE = False
    tk = None
    ttk = None
    scrolledtext = None
    messagebox = None
    filedialog = None
    _tkinter_error_message = (
        "\n"
        + "=" * 70
        + "\nERROR: tkinter is not installed\n"
        + "=" * 70
        + "\n\nThe GUI requires tkinter to run. Please install it:\n"
        + "\n  On Ubuntu/Debian/Raspberry Pi OS:\n"
        + "    sudo apt-get update\n"
        + "    sudo apt-get install python3-tk\n"
        + "\n  On Fedora:\n"
        + "    sudo dnf install python3-tkinter\n"
        + "\n  On Arch Linux:\n"
        + "    sudo pacman -S tk\n"
        + "\n  On macOS (using Homebrew):\n"
        + "    brew install python-tk\n"
        + "\nAlternatively, use the web-based GUI instead:\n"
        + "    ./start_web_gui.sh\n"
        + "=" * 70
        + "\n"
    )

import threading
import queue
import time
import psutil
import logging
from datetime import datetime
from typing import Tuple
import json

# Import the trading bot
from main import (
    TradingBot,
    PAPER_TRADING_MODE,
    SCHWAB_SANDBOX_MODE,
    BOT_MIN_ALLOCATION,
    BOT_MAX_ALLOCATION,
    SCHWAB_API_KEY,
    SCHWAB_APP_SECRET,
    SCHWAB_ACCOUNT_ID,
    SCHWAB_CALLBACK_URL,
    SCHWAB_CREDENTIAL_PLACEHOLDERS,
    SCHWAB_API_ENABLED,
    YFINANCE_AVAILABLE,
    ALLOW_RANDOM_FALLBACK,
    EXIT_REFRESH_PRICE,
    validate_configuration
)

# Configure GUI logging
gui_logger = logging.getLogger('gui')
gui_logger.setLevel(logging.INFO)


class ResourceMonitor:
    """Monitor system resources (CPU, RAM, Network, Disk)"""
    
    def __init__(self):
        self.cpu_percent = 0.0
        self.memory_percent = 0.0
        self.disk_percent = 0.0
        self.network_io = {'sent': 0, 'recv': 0}
        self.last_net_io = None
        
    def update(self):
        """Update all resource metrics"""
        # CPU usage
        self.cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        self.disk_percent = disk.percent
        
        # Network I/O (bytes per second)
        net_io = psutil.net_io_counters()
        if self.last_net_io:
            self.network_io['sent'] = net_io.bytes_sent - self.last_net_io.bytes_sent
            self.network_io['recv'] = net_io.bytes_recv - self.last_net_io.bytes_recv
        self.last_net_io = net_io
        
    def get_bottlenecks(self) -> list:
        """Detect resource bottlenecks"""
        bottlenecks = []
        if self.cpu_percent > 80:
            bottlenecks.append(f"CPU: {self.cpu_percent:.1f}%")
        if self.memory_percent > 80:
            bottlenecks.append(f"RAM: {self.memory_percent:.1f}%")
        if self.disk_percent > 90:
            bottlenecks.append(f"Disk: {self.disk_percent:.1f}%")
        return bottlenecks


class PDTTracker:
    """Track Pattern Day Trading rules compliance"""
    
    def __init__(self, starting_capital: float = 10000.0):
        self.starting_capital = starting_capital
        self.current_capital = starting_capital
        self.day_trades = []  # List of (date, symbol) tuples for last 5 business days
        self.capital_floor = starting_capital * 0.10  # 10% floor
        
    def add_day_trade(self, symbol: str):
        """Add a day trade (buy and sell same day)"""
        today = datetime.now().date()
        self.day_trades.append((today, symbol))
        
        # Keep only last 5 business days for PDT rule using pandas BDay
        from pandas.tseries.offsets import BDay
        import pandas as pd
        cutoff = (pd.Timestamp.now() - BDay(5)).date()
        self.day_trades = [(date, sym) for date, sym in self.day_trades if date >= cutoff]
    
    def get_day_trade_count(self) -> int:
        """Get number of day trades in last 5 business days"""
        return len(self.day_trades)
    
    def can_day_trade(self) -> tuple[bool, str]:
        """Check if day trading is allowed"""
        count = self.get_day_trade_count()
        
        # PDT rule: More than 3 day trades in 5 business days requires $25k
        if count >= 3 and self.current_capital < 25000:
            return False, f"PDT Limit Reached: {count}/3 day trades (need $25k+ for more)"
        
        # Check capital floor
        if self.current_capital < self.capital_floor:
            return False, f"Capital below 10% floor (${self.current_capital:.2f} < ${self.capital_floor:.2f})"
        
        return True, f"OK: {count}/3 day trades"
    
    def update_capital(self, new_capital: float):
        """Update current capital"""
        self.current_capital = new_capital


class TradingBotGUI:
    """Main GUI application for the trading bot"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Market Pie5 Trading Bot")
        self.root.geometry("1024x768")
        
        # Initialize components
        self.bot = None
        self.bot_thread = None
        self.is_running = False
        self.is_running_lock = threading.Lock()  # Thread safety for is_running flag
        self.log_queue = queue.Queue()
        self.resource_monitor = ResourceMonitor()
        # Initialize PDT tracker with capital from env (defaults to 10000, not 500)
        # This matches the default in main.py TradingBot
        try:
            default_capital = float(os.getenv('BOT_TOTAL_CAPITAL', '10000'))
            if default_capital <= 0:
                raise ValueError(f"BOT_TOTAL_CAPITAL must be positive, got {default_capital}")
        except (ValueError, TypeError) as e:
            default_capital = 10000.0
            messagebox.showwarning(
                "Config Warning", 
                f"Invalid BOT_TOTAL_CAPITAL in environment - using $10,000 default\n\nError: {e}"
            )
        self.pdt_tracker = PDTTracker(starting_capital=default_capital)
        
        # Validation state
        self.validation_errors = []
        
        # Create GUI
        self.create_menu()
        self.create_widgets()
        
        # Validate parameters before starting background threads
        if not self.validate_params():
            # Validation failed - disable start button and show error
            self.start_button.config(state=tk.DISABLED)
            # Log initial validation failure
            self.log("[ERROR] Configuration validation failed - please fix issues before starting bot")
        else:
            # Validation passed - start update loops
            self.update_logs()
            self.update_resources()
            self.update_intelligence()  # Phase 3.3: Update intelligence panel
    
    def validate_params(self) -> bool:
        """
        Validate GUI parameters before starting background threads.
        
        Checks for:
        - Placeholder values in environment variables (production mode only)
        - Non-numeric values in numeric fields
        - Configuration conflicts using validate_configuration()
        
        Returns:
            True if all validations pass, False otherwise
        """
        # Maximum number of issues to display in error popup
        MAX_DISPLAYED_ISSUES = 5
        
        issues = []
        
        # In production mode, do a quick pre-check for placeholder values
        # This provides early feedback before starting background threads
        # The full validation (including all configs) is done via validate_configuration()
        if not PAPER_TRADING_MODE:
            # Check Schwab credentials using shared placeholder list
            if SCHWAB_API_KEY in SCHWAB_CREDENTIAL_PLACEHOLDERS:
                issues.append("SCHWAB_API_KEY is not configured or is a placeholder value")
            if SCHWAB_APP_SECRET in SCHWAB_CREDENTIAL_PLACEHOLDERS:
                issues.append("SCHWAB_APP_SECRET is not configured or is a placeholder value")
            
            # Check callback URL and account ID for common placeholders
            # Note: These aren't in SCHWAB_CREDENTIAL_PLACEHOLDERS but have their own defaults
            if not SCHWAB_CALLBACK_URL or SCHWAB_CALLBACK_URL == 'your_redirect_uri':
                issues.append("SCHWAB_CALLBACK_URL is not configured or is a placeholder value")
            if not SCHWAB_ACCOUNT_ID or SCHWAB_ACCOUNT_ID == 'your_account_number':
                issues.append("SCHWAB_ACCOUNT_ID is not configured or is a placeholder value")
        
        # AI features use the ALFa AI brain (LiteLLM) and degrade gracefully,
        # so no AI credential is validated here.
        
        # Validate numeric configuration from environment
        try:
            capital = float(os.getenv('BOT_TOTAL_CAPITAL', '10000'))
            if capital <= 0:
                issues.append(f"BOT_TOTAL_CAPITAL must be positive, got {capital}")
            else:
                # Sync PDT tracker with validated capital to ensure consistency
                self.pdt_tracker.starting_capital = capital
                self.pdt_tracker.update_capital(capital)
                self.pdt_tracker.capital_floor = capital * 0.10
        except (ValueError, TypeError) as e:
            issues.append(f"BOT_TOTAL_CAPITAL must be a valid number: {e}")
        
        try:
            min_alloc = float(os.getenv('BOT_MIN_ALLOCATION', '100'))
            if min_alloc <= 0:
                issues.append(f"BOT_MIN_ALLOCATION must be positive, got {min_alloc}")
        except (ValueError, TypeError):
            issues.append(f"BOT_MIN_ALLOCATION must be a valid number")
        
        try:
            max_alloc = float(os.getenv('BOT_MAX_ALLOCATION', '5000'))
            if max_alloc <= 0:
                issues.append(f"BOT_MAX_ALLOCATION must be positive, got {max_alloc}")
        except (ValueError, TypeError):
            issues.append(f"BOT_MAX_ALLOCATION must be a valid number")
        
        # Use validate_configuration from main.py for comprehensive validation
        # This checks all config parameters, conflicts, and requirements
        is_valid, config_issues = validate_configuration()
        if not is_valid:
            issues.extend(config_issues)
        
        # If there are issues, show error popup and return False
        if issues:
            error_msg = "Configuration validation failed:\n\n"
            error_msg += "\n".join(f"• {issue}" for issue in issues[:MAX_DISPLAYED_ISSUES])
            if len(issues) > MAX_DISPLAYED_ISSUES:
                error_msg += f"\n\n... and {len(issues) - MAX_DISPLAYED_ISSUES} more issue(s)"
            error_msg += "\n\nPlease update .env or settings before starting the bot."
            
            messagebox.showerror("Invalid Configuration", error_msg)
            return False
        
        return True
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import TOS CSV", command=self.import_tos_csv)
        file_menu.add_command(label="Export Settings", command=self.export_settings)
        file_menu.add_command(label="Import Settings", command=self.import_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="PDT Rules", command=self.show_pdt_info)
    
    def create_widgets(self):
        """Create main GUI widgets"""
        # Create notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Control Panel
        control_frame = ttk.Frame(notebook)
        notebook.add(control_frame, text="Control")
        self.create_control_panel(control_frame)
        
        # Tab 2: Settings
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self.create_settings_panel(settings_frame)
        
        # Tab 3: Logs
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="Logs")
        self.create_logs_panel(logs_frame)
        
        # Tab 4: Resources
        resources_frame = ttk.Frame(notebook)
        notebook.add(resources_frame, text="Resources")
        self.create_resources_panel(resources_frame)
        
        # Tab 5: Statistics
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistics")
        self.create_stats_panel(stats_frame)
        
        # Tab 6: Market Intelligence (Phase 3.3)
        intelligence_frame = ttk.Frame(notebook)
        notebook.add(intelligence_frame, text="Intelligence")
        self.create_intelligence_panel(intelligence_frame)
        
        # Footer
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        footer_label = ttk.Label(
            footer_frame, 
            text="Created by Curt Alfrey (https://github.com/operator)",
            font=("Arial", 9),
            foreground="gray"
        )
        footer_label.pack()
    
    def create_control_panel(self, parent):
        """Create control panel with start/stop buttons"""
        # Status section
        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="● Stopped", font=("Arial", 14, "bold"), foreground="red")
        self.status_label.pack()
        
        self.pdt_status_label = ttk.Label(status_frame, text="PDT: Not checked", font=("Arial", 10))
        self.pdt_status_label.pack()
        
        # Control buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=20)
        
        self.start_button = ttk.Button(button_frame, text="Start Bot", command=self.start_bot, width=20)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Bot", command=self.stop_bot, state=tk.DISABLED, width=20)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Quick stats
        stats_frame = ttk.LabelFrame(parent, text="Quick Stats", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.total_trades_label = ttk.Label(stats_frame, text="Total Trades: 0", font=("Arial", 12))
        self.total_trades_label.pack(anchor=tk.W, pady=2)
        
        self.win_rate_label = ttk.Label(stats_frame, text="Win Rate: 0.0%", font=("Arial", 12))
        self.win_rate_label.pack(anchor=tk.W, pady=2)
        
        self.allocation_label = ttk.Label(stats_frame, text=f"Current Allocation: ${BOT_MIN_ALLOCATION:.2f}", font=("Arial", 12))
        self.allocation_label.pack(anchor=tk.W, pady=2)
        
        # Get default capital from env variable (matches main.py)
        default_capital = float(os.getenv('BOT_TOTAL_CAPITAL', '10000'))
        self.capital_label = ttk.Label(stats_frame, text=f"Capital: ${default_capital:.2f}", font=("Arial", 12))
        self.capital_label.pack(anchor=tk.W, pady=2)
    
    def create_settings_panel(self, parent):
        """Create settings configuration panel"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bot settings
        bot_frame = ttk.LabelFrame(scrollable_frame, text="Bot Settings", padding=10)
        bot_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Get default capital from env variable (matches main.py)
        default_capital = float(os.getenv('BOT_TOTAL_CAPITAL', '10000'))
        ttk.Label(bot_frame, text="Total Capital:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.capital_var = tk.StringVar(value=str(default_capital))
        ttk.Entry(bot_frame, textvariable=self.capital_var, width=20).grid(row=0, column=1, pady=2)
        
        ttk.Label(bot_frame, text="Min Allocation:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.min_alloc_var = tk.StringVar(value=str(BOT_MIN_ALLOCATION))
        ttk.Entry(bot_frame, textvariable=self.min_alloc_var, width=20).grid(row=1, column=1, pady=2)
        
        ttk.Label(bot_frame, text="Max Allocation:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.max_alloc_var = tk.StringVar(value=str(BOT_MAX_ALLOCATION))
        ttk.Entry(bot_frame, textvariable=self.max_alloc_var, width=20).grid(row=2, column=1, pady=2)
        
        ttk.Label(bot_frame, text="Trailing Stop %:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.trail_stop_var = tk.StringVar(value="5.0")
        ttk.Entry(bot_frame, textvariable=self.trail_stop_var, width=20).grid(row=3, column=1, pady=2)
        
        # Risk settings
        risk_frame = ttk.LabelFrame(scrollable_frame, text="Risk Settings", padding=10)
        risk_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(risk_frame, text="Risk Threshold %:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.risk_threshold_var = tk.StringVar(value="5.0")
        ttk.Entry(risk_frame, textvariable=self.risk_threshold_var, width=20).grid(row=0, column=1, pady=2)
        
        ttk.Label(risk_frame, text="Max Positions:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_positions_var = tk.StringVar(value="5")
        ttk.Entry(risk_frame, textvariable=self.max_positions_var, width=20).grid(row=1, column=1, pady=2)
        
        # PDT settings
        pdt_frame = ttk.LabelFrame(scrollable_frame, text="PDT Compliance", padding=10)
        pdt_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Show PDT status based on trading mode
        pdt_info_label = ttk.Label(pdt_frame, text=f"PDT Protection: {'Enabled (Production Mode)' if not PAPER_TRADING_MODE else 'Disabled (Paper/Sandbox Mode)'}")
        pdt_info_label.pack(anchor=tk.W, pady=2)
        
        if not PAPER_TRADING_MODE:
            ttk.Label(pdt_frame, text="⚠ PDT rules are enforced in production mode", foreground="orange").pack(anchor=tk.W, pady=2)
        else:
            ttk.Label(pdt_frame, text="✓ Unlimited day trades allowed in paper/sandbox mode", foreground="green").pack(anchor=tk.W, pady=2)
        
        # Capital Floor setting (use pack to avoid geometry manager conflict)
        capital_floor_container = ttk.Frame(pdt_frame)
        capital_floor_container.pack(fill=tk.X, pady=2)
        ttk.Label(capital_floor_container, text="Capital Floor % (auto-pause):").pack(side=tk.LEFT, padx=(0, 5))
        self.capital_floor_var = tk.StringVar(value="10.0")
        ttk.Entry(capital_floor_container, textvariable=self.capital_floor_var, width=20).pack(side=tk.LEFT)
        
        # Alert settings
        alert_frame = ttk.LabelFrame(scrollable_frame, text="Alerts", padding=10)
        alert_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.enable_alerts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(alert_frame, text="Enable Alerts", variable=self.enable_alerts_var).pack(anchor=tk.W)
        
        # Alert Email setting (use pack to avoid geometry manager conflict)
        alert_email_container = ttk.Frame(alert_frame)
        alert_email_container.pack(fill=tk.X, pady=2)
        ttk.Label(alert_email_container, text="Alert Email:").pack(side=tk.LEFT, padx=(0, 5))
        self.alert_email_var = tk.StringVar(value="")
        ttk.Entry(alert_email_container, textvariable=self.alert_email_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Validation status frame
        validation_frame = ttk.LabelFrame(scrollable_frame, text="Settings Validation", padding=10)
        validation_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.validation_status_label = ttk.Label(
            validation_frame, 
            text="✓ All settings are valid", 
            foreground="green",
            font=("Arial", 10, "bold")
        )
        self.validation_status_label.pack(anchor=tk.W, pady=2)
        
        # Apply button
        ttk.Button(scrollable_frame, text="Apply Settings", command=self.apply_settings).pack(pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_logs_panel(self, parent):
        """Create logs viewer panel"""
        # Log text area
        self.log_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, height=30)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Clear button
        ttk.Button(parent, text="Clear Logs", command=self.clear_logs).pack(pady=5)
    
    def create_resources_panel(self, parent):
        """Create resource monitoring panel"""
        # Resource metrics
        metrics_frame = ttk.LabelFrame(parent, text="System Resources", padding=10)
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.cpu_label = ttk.Label(metrics_frame, text="CPU: 0%", font=("Arial", 12))
        self.cpu_label.pack(anchor=tk.W, pady=2)
        self.cpu_progress = ttk.Progressbar(metrics_frame, length=400, mode='determinate')
        self.cpu_progress.pack(pady=2)
        
        self.memory_label = ttk.Label(metrics_frame, text="Memory: 0%", font=("Arial", 12))
        self.memory_label.pack(anchor=tk.W, pady=2)
        self.memory_progress = ttk.Progressbar(metrics_frame, length=400, mode='determinate')
        self.memory_progress.pack(pady=2)
        
        self.disk_label = ttk.Label(metrics_frame, text="Disk: 0%", font=("Arial", 12))
        self.disk_label.pack(anchor=tk.W, pady=2)
        self.disk_progress = ttk.Progressbar(metrics_frame, length=400, mode='determinate')
        self.disk_progress.pack(pady=2)
        
        self.network_label = ttk.Label(metrics_frame, text="Network: ↑0 KB/s ↓0 KB/s", font=("Arial", 12))
        self.network_label.pack(anchor=tk.W, pady=2)
        
        # Bottleneck warnings
        warning_frame = ttk.LabelFrame(parent, text="Resource Warnings", padding=10)
        warning_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.warning_text = scrolledtext.ScrolledText(warning_frame, wrap=tk.WORD, height=10)
        self.warning_text.pack(fill=tk.BOTH, expand=True)
    
    def create_stats_panel(self, parent):
        """Create detailed statistics panel"""
        stats_text_frame = ttk.Frame(parent)
        stats_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.stats_text = scrolledtext.ScrolledText(stats_text_frame, wrap=tk.WORD, height=30)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(parent, text="Refresh Statistics", command=self.refresh_stats).pack(pady=5)
    
    def create_intelligence_panel(self, parent):
        """Create Market Intelligence panel - Phase 3.3
        
        Displays:
        - Alert history (desktop notifications sent in last 24 hours)
        - Market intelligence events (M&A, IPO, Regulatory)
        - Filter effectiveness statistics
        """
        # Create tabs within this panel
        intel_notebook = ttk.Notebook(parent)
        intel_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Alert History
        alerts_frame = ttk.Frame(intel_notebook)
        intel_notebook.add(alerts_frame, text="Alerts (24h)")
        self.create_alerts_subtab(alerts_frame)
        
        # Tab 2: Market Events
        events_frame = ttk.Frame(intel_notebook)
        intel_notebook.add(events_frame, text="Market Events")
        self.create_events_subtab(events_frame)
        
        # Tab 3: Filter Statistics
        filter_frame = ttk.Frame(intel_notebook)
        intel_notebook.add(filter_frame, text="Filter Stats")
        self.create_filter_stats_subtab(filter_frame)
    
    def create_alerts_subtab(self, parent):
        """Display alert history from AlertManager"""
        # Header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="Desktop Notifications (Last 24 Hours)", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Real-time popup alerts for trades, sizzle stocks, and filter blocks", font=("Arial", 9), foreground="gray").pack(anchor=tk.W)
        
        # Alerts display
        alerts_text_frame = ttk.Frame(parent)
        alerts_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.alerts_text = scrolledtext.ScrolledText(alerts_text_frame, wrap=tk.WORD, height=25, font=("Courier", 9))
        self.alerts_text.pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Refresh Alert History", command=self.refresh_alerts).pack(side=tk.LEFT, padx=5)
        ttk.Label(button_frame, text="Updates automatically every 10 seconds", font=("Arial", 9), foreground="gray").pack(side=tk.LEFT, padx=20)
    
    def create_events_subtab(self, parent):
        """Display market intelligence events (M&A, IPO, Regulatory)"""
        # Header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="Market Intelligence Events", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text="High-impact news: M&A deals, IPOs, Regulatory events from 5 news sources", font=("Arial", 9), foreground="gray").pack(anchor=tk.W)
        
        # Events display
        events_text_frame = ttk.Frame(parent)
        events_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.events_text = scrolledtext.ScrolledText(events_text_frame, wrap=tk.WORD, height=25, font=("Courier", 9))
        self.events_text.pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Refresh Market Events", command=self.refresh_events).pack(side=tk.LEFT, padx=5)
        ttk.Label(button_frame, text="Updates every 60 seconds from news daemon", font=("Arial", 9), foreground="gray").pack(side=tk.LEFT, padx=20)
    
    def create_filter_stats_subtab(self, parent):
        """Display filter block statistics"""
        # Header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="Filter Effectiveness", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Trades blocked by each filter - helps understand filter impact", font=("Arial", 9), foreground="gray").pack(anchor=tk.W)
        
        # Stats display
        stats_text_frame = ttk.Frame(parent)
        stats_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.filter_stats_text = scrolledtext.ScrolledText(stats_text_frame, wrap=tk.WORD, height=25, font=("Courier", 9))
        self.filter_stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Refresh Filter Stats", command=self.refresh_filter_stats).pack(side=tk.LEFT, padx=5)
        ttk.Label(button_frame, text="Tracked from bot logs", font=("Arial", 9), foreground="gray").pack(side=tk.LEFT, padx=20)
    
    def validate_settings(self) -> bool:
        """
        Validate all settings and update button state.
        Returns True if all settings are valid, False otherwise.
        """
        self.validation_errors = []
        
        try:
            # Validate capital
            capital = float(self.capital_var.get())
            if capital <= 0:
                self.validation_errors.append("Total Capital must be positive")
            elif capital < 100:
                self.validation_errors.append("Total Capital should be at least $100")
                
            # Validate allocations
            min_alloc = float(self.min_alloc_var.get())
            max_alloc = float(self.max_alloc_var.get())
            
            if min_alloc <= 0:
                self.validation_errors.append("Min Allocation must be positive")
            if max_alloc <= 0:
                self.validation_errors.append("Max Allocation must be positive")
            if min_alloc >= max_alloc:
                self.validation_errors.append("Min Allocation must be less than Max Allocation")
            if max_alloc > capital:
                self.validation_errors.append("Max Allocation cannot exceed Total Capital")
                
            # Validate trailing stop
            trail_stop = float(self.trail_stop_var.get())
            if trail_stop <= 0 or trail_stop > 100:
                self.validation_errors.append("Trailing Stop must be between 0 and 100%")
                
            # Validate risk threshold
            risk_threshold = float(self.risk_threshold_var.get())
            if risk_threshold <= 0 or risk_threshold > 100:
                self.validation_errors.append("Risk Threshold must be between 0 and 100%")
                
            # Validate max positions
            max_positions = int(self.max_positions_var.get())
            if max_positions <= 0:
                self.validation_errors.append("Max Positions must be positive")
                
            # Validate capital floor
            capital_floor = float(self.capital_floor_var.get())
            if capital_floor <= 0 or capital_floor > 100:
                self.validation_errors.append("Capital Floor must be between 0 and 100%")
                
        except ValueError:
            self.validation_errors.append("Please enter valid numbers for all fields")
        
        # Update validation status label
        if self.validation_errors:
            error_summary = self.validation_errors[0] if len(self.validation_errors) == 1 else f"{len(self.validation_errors)} validation errors"
            self.validation_status_label.config(
                text=f"✗ {error_summary}",
                foreground="red"
            )
        else:
            self.validation_status_label.config(
                text="✓ All settings are valid",
                foreground="green"
            )
        
        # Update Start button state based on validation
        if self.validation_errors:
            self.start_button.config(state=tk.DISABLED)
            return False
        else:
            # Only enable if not currently running
            if not self.is_running:
                self.start_button.config(state=tk.NORMAL)
            return True
    
    def get_mode_description(self) -> Tuple[str, str]:
        """
        Get the current trading mode description.
        
        Returns:
            Tuple[str, str]: A tuple of (mode_name, mode_description) where:
                - mode_name: Human-readable name (e.g., "Live Trading", "Sandbox Mode", "Simulation Mode")
                - mode_description: Explanation of what the mode does
        """
        if not PAPER_TRADING_MODE:
            return ("Live Trading", "Real money will be used via Schwab Production API")
        elif SCHWAB_SANDBOX_MODE:
            return ("Sandbox Mode", "Testing with Schwab Sandbox API (paperMoney)")
        else:
            return ("Simulation Mode", "Local simulation without API calls")
    
    def start_bot(self):
        """Start the trading bot"""
        # Check if already running or previous thread still alive
        with self.is_running_lock:
            if self.is_running:
                return
            
            # Check if previous thread is still running
            if self.bot_thread and self.bot_thread.is_alive():
                self.log("[BOT] Previous bot thread still running, please wait...")
                return
        
        # Validate settings first (before setting is_running flag)
        if not self.validate_settings():
            error_msg = "Cannot start bot - invalid settings:\n\n" + "\n".join(self.validation_errors)
            messagebox.showerror("Invalid Settings", error_msg)
            self.log("[BOT] Start cancelled - invalid settings")
            for error in self.validation_errors:
                self.log(f"[ERROR] {error}")
            return
        
        # Get settings
        capital = float(self.capital_var.get())
        min_alloc = float(self.min_alloc_var.get())
        max_alloc = float(self.max_alloc_var.get())
        trail_stop = float(self.trail_stop_var.get())
        
        # Get mode description
        mode_name, mode_desc = self.get_mode_description()
        
        # Build confirmation message based on mode
        if not PAPER_TRADING_MODE:
            # Live mode - strong warning
            confirmation_msg = (
                "!!! LIVE TRADING MODE !!!\n\n"
                "⚠️  Real money will be used for trades!\n"
                "⚠️  Schwab Production API will be used\n\n"
                f"Capital: ${capital:.2f}\n"
                f"Min Allocation: ${min_alloc:.2f}\n"
                f"Max Allocation: ${max_alloc:.2f}\n"
                f"Trailing Stop: {trail_stop}%\n\n"
                "Are you ABSOLUTELY SURE you want to proceed with LIVE trading?"
            )
            icon = 'warning'
        elif SCHWAB_SANDBOX_MODE:
            # Sandbox mode - informational
            confirmation_msg = (
                "Starting bot in Sandbox Mode\n\n"
                f"Mode: {mode_name}\n"
                f"Description: {mode_desc}\n\n"
                f"Capital: ${capital:.2f}\n"
                f"Min Allocation: ${min_alloc:.2f}\n"
                f"Max Allocation: ${max_alloc:.2f}\n"
                f"Trailing Stop: {trail_stop}%\n\n"
                "Trades will be sent to Schwab Sandbox API.\n"
                "Orders will be visible in ThinkorSwim paperMoney.\n\n"
                "Do you want to start the bot?"
            )
            icon = 'question'
        else:
            # Simulation mode - informational
            confirmation_msg = (
                "Starting bot in Simulation Mode\n\n"
                f"Mode: {mode_name}\n"
                f"Description: {mode_desc}\n\n"
                f"Capital: ${capital:.2f}\n"
                f"Min Allocation: ${min_alloc:.2f}\n"
                f"Max Allocation: ${max_alloc:.2f}\n"
                f"Trailing Stop: {trail_stop}%\n\n"
                "Local simulation only - no API calls.\n"
                "No real or sandbox orders will be placed.\n\n"
                "Do you want to start the bot?"
            )
            icon = 'question'
        
        # Show confirmation dialog
        confirm = messagebox.askyesno(
            f"Confirm Start - {mode_name}",
            confirmation_msg,
            icon=icon
        )
        
        if not confirm:
            self.log(f"[BOT] Bot start cancelled by user ({mode_name})")
            return
        
        # Check PDT compliance only in production mode
        if not PAPER_TRADING_MODE:
            can_trade, msg = self.pdt_tracker.can_day_trade()
            if not can_trade:
                messagebox.showwarning("PDT Warning", msg)
                self.log(f"[PDT WARNING] {msg}")
                return
        
        # All validations passed - now set is_running flag
        with self.is_running_lock:
            self.is_running = True
        
        # Update UI to show running state
        self.status_label.config(text="● Running", foreground="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Initialize bot
        self.bot = TradingBot(total_capital=capital)
        
        self.pdt_tracker.update_capital(capital)
        
        self.log("[BOT] Starting trading bot...")
        self.log(f"[BOT] Mode: {mode_name}")
        self.log(f"[BOT] Description: {mode_desc}")
        self.log(f"[BOT] Capital: ${capital:.2f}")
        pdt_enabled = not PAPER_TRADING_MODE
        self.log(f"[BOT] PDT Protection: {'Enabled (Production Mode)' if pdt_enabled else 'Disabled (Paper/Sandbox Mode)'}")
        
        # Start bot in separate thread
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()
    
    def stop_bot(self):
        """Stop the trading bot"""
        with self.is_running_lock:
            if not self.is_running:
                return
            
            self.is_running = False
        
        self.status_label.config(text="● Stopping...", foreground="orange")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        
        self.log("[BOT] Stopping trading bot...")
        
        # Wait for bot thread to finish (with timeout)
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=5.0)
            if self.bot_thread.is_alive():
                self.log("[BOT] Warning: Bot thread did not stop cleanly")
        
        self.status_label.config(text="● Stopped", foreground="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def run_bot(self):
        """Run the trading bot (in separate thread)"""
        try:
            # Load symbols
            symbols = self.bot.load_scan_symbols()
            
            for symbol in symbols:
                # Check is_running flag with thread safety
                with self.is_running_lock:
                    if not self.is_running:
                        break
                
                # Get strategy signal (BUY/SELL/HOLD) and price/volume
                try:
                    signal, price, volume = self.bot.get_strategy_signal(symbol, use_random_fallback=True)
                except Exception as e:
                    self.log(f"Error getting strategy signal for {symbol}: {e}")
                    time.sleep(2)
                    continue
                
                if signal == 'HOLD':
                    self.log(f"[SIGNAL] {symbol} HOLD — skipping")
                    time.sleep(2)
                    continue
                if price is None or volume is None:
                    self.log(f"[SIGNAL] {symbol} {signal} but no price/volume — skipping")
                    time.sleep(2)
                    continue
                action = self.bot._signal_to_action(symbol, signal)
                if action is None:
                    self.log(f"[SIGNAL] {symbol} {signal} — no action (position state); skipping")
                    time.sleep(2)
                    continue
                self.log(f"Retrieved {symbol}: ${price:.2f}, signal: {signal} → action: {action}")
                if EXIT_REFRESH_PRICE and action in ('SELL', 'COVER'):
                    try:
                        exit_price, _ = self.bot.get_stock_price(symbol, use_random_fallback=False)
                        if exit_price is not None:
                            price = exit_price
                    except (ValueError, TypeError):
                        pass
                # Execute trade (BUY, SELL, SHORT, or COVER)
                result = self.bot.execute_trade(symbol, action, price, volume=volume)
                
                # Log trade result and track day trades for PDT compliance
                if result:
                    status = result.get('status', 'unknown')
                    if status == 'skipped':
                        reason = result.get('reason', 'unknown')
                        self.log(f"[TRADE] {symbol} trade skipped: {reason}")
                    elif status == 'paused':
                        self.log(f"[TRADE] {symbol} trade paused: {result.get('message', 'capital floor')}")
                        with self.is_running_lock:
                            self.is_running = False  # Stop trading loop
                        break
                    elif status == 'simulated':
                        self.log(f"[TRADE] {symbol} {action} executed at ${price:.2f}")
                        # Note: PDT tracking is handled internally by the bot's execute_trade_paper_mode
                        # when positions are closed (sold), not when they are opened (bought).
                        # A day trade only counts when a position is bought AND sold on the same day.
                
                # Update GUI and PDT tracker with current capital
                self.update_bot_stats()
                self.pdt_tracker.update_capital(self.bot.total_capital)
                self.root.after(0, lambda: self.capital_label.config(
                    text=f"Capital: ${self.bot.total_capital:.2f}"
                ))
                
                # Sleep
                time.sleep(2)
            
            self.log("[BOT] Trading cycle completed")
            
        except Exception as e:
            self.log(f"[ERROR] Bot error: {str(e)}")
        finally:
            with self.is_running_lock:
                self.is_running = False
            self.root.after(0, lambda: self.status_label.config(text="● Stopped", foreground="red"))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
    
    def update_bot_stats(self):
        """Update bot statistics in GUI"""
        if not self.bot:
            return
        
        track = self.bot.track_record
        
        self.root.after(0, lambda: self.total_trades_label.config(
            text=f"Total Trades: {track['total_trades']}"
        ))
        self.root.after(0, lambda: self.win_rate_label.config(
            text=f"Win Rate: {track['win_rate']*100:.1f}%"
        ))
        self.root.after(0, lambda: self.allocation_label.config(
            text=f"Current Allocation: ${track['current_allocation']:.2f}"
        ))
    
    
    def update_pdt_tracker_capital(self, capital: float, capital_floor_pct: float):
        """
        Update PDT tracker with new capital and floor values.
        
        Args:
            capital: Total capital amount in dollars
            capital_floor_pct: Capital floor as a percentage (0-100), not decimal (0-1)
        """
        self.pdt_tracker.starting_capital = capital
        self.pdt_tracker.update_capital(capital)
        self.pdt_tracker.capital_floor = capital * (capital_floor_pct / 100.0)
        self.log(f"[SETTINGS] Updated PDT tracker capital to ${capital:.2f}")
    
    def load_settings(self):
        """Load settings from settings.json if it exists"""
        settings_file = 'settings.json'
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Apply loaded settings to GUI fields with validation
                if 'capital' in settings:
                    try:
                        capital = float(settings['capital'])
                        if capital <= 0:
                            raise ValueError("Capital must be positive")
                        self.capital_var.set(str(capital))
                        # Update PDT tracker with loaded capital
                        capital_floor_pct = float(settings.get('capital_floor', 10.0))
                        self.update_pdt_tracker_capital(capital, capital_floor_pct)
                    except (ValueError, TypeError) as e:
                        self.log(f"[SETTINGS WARNING] Invalid capital value, using default: {e}")
                
                if 'min_allocation' in settings:
                    self.min_alloc_var.set(str(settings['min_allocation']))
                if 'max_allocation' in settings:
                    self.max_alloc_var.set(str(settings['max_allocation']))
                if 'trailing_stop' in settings:
                    self.trail_stop_var.set(str(settings['trailing_stop']))
                if 'risk_threshold' in settings:
                    self.risk_threshold_var.set(str(settings['risk_threshold']))
                if 'max_positions' in settings:
                    self.max_positions_var.set(str(settings['max_positions']))
                if 'capital_floor' in settings:
                    self.capital_floor_var.set(str(settings['capital_floor']))
                if 'enable_alerts' in settings:
                    self.enable_alerts_var.set(settings['enable_alerts'])
                if 'alert_email' in settings:
                    self.alert_email_var.set(settings['alert_email'])
                
                self.log(f"[SETTINGS] Loaded settings from {settings_file}")
            else:
                self.log("[SETTINGS] No saved settings found, using defaults")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.log(f"[SETTINGS ERROR] Failed to read settings file: {str(e)}")
            messagebox.showerror("Load Error", f"Settings file is corrupted or missing:\n{str(e)}")
        except (OSError, IOError) as e:
            self.log(f"[SETTINGS ERROR] File system error loading settings: {str(e)}")
            messagebox.showerror("Load Error", f"Cannot access settings file:\n{str(e)}")
        except Exception as e:
            self.log(f"[SETTINGS ERROR] Unexpected error loading settings: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load settings:\n{str(e)}")
            # Continue with default values from environment/GUI
    
    def apply_settings(self):
        """Apply settings changes"""
        if self.validate_settings():
            self.log("[SETTINGS] Settings validated and applied successfully")
            messagebox.showinfo("Settings", "Settings have been validated and applied")
        else:
            error_msg = "Settings validation failed:\n\n" + "\n".join(self.validation_errors)
            messagebox.showerror("Validation Error", error_msg)
            self.log("[SETTINGS] Settings validation failed")
            for error in self.validation_errors:
                self.log(f"[ERROR] {error}")
    
    def import_tos_csv(self):
        """Import TOS CSV file"""
        filename = filedialog.askopenfilename(
            title="Select TOS CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            if not self.bot:
                self.bot = TradingBot(total_capital=float(self.capital_var.get()))
            
            trades = self.bot.import_tos_csv(filename)
            if trades:
                self.bot.process_tos_trades(trades)
                self.log(f"[TOS] Imported {len(trades)} trades from {filename}")
                self.update_bot_stats()
                messagebox.showinfo("Import Success", f"Imported {len(trades)} trades")
            else:
                messagebox.showerror("Import Error", "Failed to import trades")
    
    def export_settings(self):
        """Export current settings to JSON"""
        filename = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Validate numeric values before export
                settings = {
                    'capital': self.capital_var.get(),
                    'min_allocation': self.min_alloc_var.get(),
                    'max_allocation': self.max_alloc_var.get(),
                    'trailing_stop': self.trail_stop_var.get(),
                    'risk_threshold': self.risk_threshold_var.get(),
                    'max_positions': self.max_positions_var.get(),
                    'capital_floor': self.capital_floor_var.get(),
                    'enable_alerts': self.enable_alerts_var.get(),
                    'alert_email': self.alert_email_var.get()
                }
                
                # Validate that numeric fields can be converted
                try:
                    float(settings['capital'])
                    float(settings['min_allocation'])
                    float(settings['max_allocation'])
                    float(settings['trailing_stop'])
                    float(settings['risk_threshold'])
                    int(settings['max_positions'])
                    float(settings['capital_floor'])
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid settings values: {str(e)}")
                
                # Write to file with proper JSON encoding error handling
                try:
                    with open(filename, 'w') as f:
                        json.dump(settings, f, indent=2)
                except TypeError as e:
                    # JSON encoding errors (e.g., non-serializable types)
                    raise ValueError(f"Cannot serialize settings to JSON: {str(e)}")
                except OSError as e:
                    # File I/O errors (includes PermissionError)
                    raise IOError(f"Cannot write to file: {str(e)}")
                
                self.log(f"[SETTINGS] Exported to {filename}")
                messagebox.showinfo("Export Success", f"Settings exported to {filename}")
                
            except ValueError as e:
                # Validation or JSON encoding errors
                error_msg = str(e)
                self.log(f"[SETTINGS ERROR] {error_msg}")
                messagebox.showerror("Export Error", error_msg)
            except IOError as e:
                # File I/O errors
                error_msg = str(e)
                self.log(f"[SETTINGS ERROR] {error_msg}")
                messagebox.showerror("Export Error", error_msg)
            except Exception as e:
                # Unexpected errors
                error_msg = f"Unexpected error during export: {str(e)}"
                self.log(f"[SETTINGS ERROR] {error_msg}")
                messagebox.showerror("Export Error", error_msg)
    
    def import_settings(self):
        """Import settings from JSON"""
        filename = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    settings = json.load(f)
                
                # Validate that settings is a dictionary
                if not isinstance(settings, dict):
                    raise ValueError("Settings file must contain a JSON object")
                
                # Apply settings with defaults
                self.capital_var.set(settings.get('capital', '500.00'))
                self.min_alloc_var.set(settings.get('min_allocation', str(BOT_MIN_ALLOCATION)))
                self.max_alloc_var.set(settings.get('max_allocation', str(BOT_MAX_ALLOCATION)))
                self.trail_stop_var.set(settings.get('trailing_stop', '5.0'))
                self.risk_threshold_var.set(settings.get('risk_threshold', '5.0'))
                self.max_positions_var.set(settings.get('max_positions', '5'))
                self.capital_floor_var.set(settings.get('capital_floor', '10.0'))
                self.enable_alerts_var.set(settings.get('enable_alerts', True))
                self.alert_email_var.set(settings.get('alert_email', ''))
                
                # Validate imported settings
                if not self.validate_settings():
                    # Use getattr to safely access validation_errors
                    errors = getattr(self, 'validation_errors', ['Unknown validation error'])
                    error_msg = "Imported settings are invalid:\n\n" + "\n".join(errors)
                    self.log(f"[SETTINGS ERROR] Imported settings validation failed")
                    messagebox.showwarning("Import Warning", error_msg + "\n\nPlease review and correct the settings.")
                else:
                    self.log(f"[SETTINGS] Imported from {filename}")
                    messagebox.showinfo("Import Success", f"Settings imported from {filename}")
                
            except FileNotFoundError as e:
                error_msg = f"File not found: {str(e)}"
                self.log(f"[SETTINGS ERROR] {error_msg}")
                messagebox.showerror("Import Error", error_msg)
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON format: {str(e)}"
                self.log(f"[SETTINGS ERROR] {error_msg}")
                messagebox.showerror("Import Error", error_msg)
            except ValueError as e:
                error_msg = f"Invalid settings values: {str(e)}"
                self.log(f"[SETTINGS ERROR] {error_msg}")
                messagebox.showerror("Import Error", error_msg)
            except (OSError, IOError) as e:
                error_msg = f"Cannot read file: {str(e)}"
                self.log(f"[SETTINGS ERROR] {error_msg}")
                messagebox.showerror("Import Error", error_msg)
            except Exception as e:
                error_msg = f"Failed to import settings: {str(e)}"
                self.log(f"[SETTINGS ERROR] {error_msg}")
                messagebox.showerror("Import Error", error_msg)
    
    def log(self, message: str):
        """Add message to log queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")
    
    def update_logs(self):
        """Update log display from queue"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        except Exception as e:
            # Handle unexpected errors to prevent UI freezing
            error_msg = f"Unexpected error in log update: {str(e)}"
            gui_logger.error(error_msg)
            try:
                # Try to show error in GUI if possible
                messagebox.showerror("Log Error", error_msg)
            except Exception:
                # If messagebox also fails, just log it
                gui_logger.error("Failed to show error messagebox")
        
        # Schedule next update
        try:
            self.root.after(100, self.update_logs)
        except Exception as e:
            gui_logger.error(f"Failed to schedule log update: {e}")
    
    def clear_logs(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
    
    def update_resources(self):
        """Update resource monitoring display"""
        try:
            self.resource_monitor.update()
            
            # Update labels and progress bars
            self.cpu_label.config(text=f"CPU: {self.resource_monitor.cpu_percent:.1f}%")
            self.cpu_progress['value'] = self.resource_monitor.cpu_percent
            
            self.memory_label.config(text=f"Memory: {self.resource_monitor.memory_percent:.1f}%")
            self.memory_progress['value'] = self.resource_monitor.memory_percent
            
            self.disk_label.config(text=f"Disk: {self.resource_monitor.disk_percent:.1f}%")
            self.disk_progress['value'] = self.resource_monitor.disk_percent
            
            sent_kb = self.resource_monitor.network_io['sent'] / 1024
            recv_kb = self.resource_monitor.network_io['recv'] / 1024
            self.network_label.config(text=f"Network: ↑{sent_kb:.1f} KB/s ↓{recv_kb:.1f} KB/s")
            
            # Check for bottlenecks
            bottlenecks = self.resource_monitor.get_bottlenecks()
            if bottlenecks:
                timestamp = datetime.now().strftime("%H:%M:%S")
                warning = f"[{timestamp}] WARNING: Resource bottlenecks detected:\n"
                for b in bottlenecks:
                    warning += f"  - {b}\n"
                self.warning_text.insert(tk.END, warning)
                self.warning_text.see(tk.END)
                
                # Notify bot about resource bottlenecks if available
                if self.bot and hasattr(self.bot, 'handle_resource_bottleneck'):
                    try:
                        self.bot.handle_resource_bottleneck(bottlenecks)
                    except Exception as e:
                        gui_logger.warning(f"Failed to notify bot about resource bottlenecks: {e}")
            
            # Update PDT status (only relevant in production mode)
            if not PAPER_TRADING_MODE:
                can_trade, msg = self.pdt_tracker.can_day_trade()
                self.pdt_status_label.config(
                    text=f"PDT: {msg}",
                    foreground="green" if can_trade else "red"
                )
            else:
                self.pdt_status_label.config(
                    text="PDT: Not enforced (paper/sandbox mode)",
                    foreground="green"
                )
        except AttributeError as e:
            # Handle missing attributes gracefully
            error_msg = f"Resource monitor attribute error: {str(e)}"
            gui_logger.error(error_msg)
        except ZeroDivisionError as e:
            # Handle potential division errors in network calculation
            error_msg = f"Division error in resource calculation: {str(e)}"
            gui_logger.error(error_msg)
        except Exception as e:
            # Handle unexpected errors to prevent UI freezing
            error_msg = f"Unexpected error in resource update: {str(e)}"
            gui_logger.error(error_msg)
            try:
                # Try to show error in GUI if possible
                messagebox.showerror("Resource Monitor Error", error_msg)
            except Exception:
                # If messagebox also fails, just log it
                gui_logger.error("Failed to show resource monitor error messagebox")
        
        # Schedule next update (always schedule even if error occurred)
        try:
            self.root.after(2000, self.update_resources)
        except Exception as e:
            gui_logger.error(f"Failed to schedule resource update: {e}")
    
    def update_intelligence(self):
        """Update Market Intelligence panel periodically (every 10 seconds)
        
        Phase 3.3: Auto-refresh alerts, market events, and filter stats
        """
        try:
            # Get current tab name to avoid unnecessary updates
            # Only refresh if user is viewing the Intelligence tab
            # This reduces CPU usage when tab is not active
            pass  # Updates happen on-demand via button clicks
        except Exception as e:
            gui_logger.debug(f"Error in intelligence update: {e}")
        
        # Schedule next update (every 10 seconds)
        try:
            self.root.after(10000, self.update_intelligence)
        except Exception as e:
            gui_logger.error(f"Failed to schedule intelligence update: {e}")
    
    def refresh_alerts(self):
        """Refresh alert history display from AlertManager"""
        self.alerts_text.delete(1.0, tk.END)
        
        try:
            # Try to import alert manager and get recent alerts
            from alert_manager import get_alert_manager
            
            alert_manager = get_alert_manager(enabled=True)
            if not alert_manager:
                self.alerts_text.insert(tk.END, "Alert system not initialized\n")
                return
            
            recent_alerts = alert_manager.get_recent_alerts(50)
            
            if not recent_alerts:
                self.alerts_text.insert(tk.END, "No alerts in history\n")
                return
            
            # Display alerts in reverse chronological order
            self.alerts_text.insert(tk.END, f"ALERT HISTORY (Last {len(recent_alerts)} alerts)\n")
            self.alerts_text.insert(tk.END, "="*70 + "\n\n")
            
            for i, alert in enumerate(reversed(recent_alerts), 1):
                timestamp = alert.get('timestamp', 'N/A')
                title = alert.get('title', 'N/A')
                message = alert.get('message', 'N/A')
                
                self.alerts_text.insert(tk.END, f"{i}. [{timestamp}] {title}\n")
                self.alerts_text.insert(tk.END, f"   {message}\n\n")
        
        except ImportError:
            self.alerts_text.insert(tk.END, "Alert system not available - ensure alert_manager.py is installed\n")
        except Exception as e:
            self.alerts_text.insert(tk.END, f"Error loading alert history: {e}\n")
    
    def refresh_events(self):
        """Refresh market intelligence events from market_intelligence.json"""
        self.events_text.delete(1.0, tk.END)
        
        try:
            import json
            from datetime import datetime
            
            intel_file = 'data/market_intelligence.json'
            if not os.path.exists(intel_file):
                self.events_text.insert(tk.END, f"Market intelligence database not found at {intel_file}\n")
                self.events_text.insert(tk.END, "Run news daemon to populate: monitoring/news_daemon.py\n")
                return
            
            with open(intel_file, 'r') as f:
                intel_data = json.load(f)
            
            # Extract high-impact events
            events = intel_data.get('events', [])
            high_impact = [e for e in events if e.get('category') in ('IPO', 'M&A', 'Regulatory')]
            
            self.events_text.insert(tk.END, f"MARKET INTELLIGENCE EVENTS\n")
            self.events_text.insert(tk.END, "="*70 + "\n\n")
            self.events_text.insert(tk.END, f"Total Events: {len(events)}\n")
            self.events_text.insert(tk.END, f"High-Impact Events: {len(high_impact)}\n\n")
            
            if high_impact:
                self.events_text.insert(tk.END, "HIGH-IMPACT EVENTS:\n")
                self.events_text.insert(tk.END, "-"*70 + "\n\n")
                
                for event in sorted(high_impact, key=lambda x: x.get('date', ''), reverse=True)[:20]:
                    category = event.get('category', 'Unknown')
                    title = event.get('title', 'No title')
                    date = event.get('date', 'N/A')
                    source = event.get('source', 'Unknown')
                    
                    self.events_text.insert(tk.END, f"[{category}] {date} ({source})\n")
                    self.events_text.insert(tk.END, f"{title}\n\n")
            else:
                self.events_text.insert(tk.END, "No high-impact events detected\n")
        
        except json.JSONDecodeError:
            self.events_text.insert(tk.END, "Error parsing market_intelligence.json\n")
        except Exception as e:
            self.events_text.insert(tk.END, f"Error loading market events: {e}\n")
    
    def refresh_filter_stats(self):
        """Refresh filter statistics from bot logs"""
        self.filter_stats_text.delete(1.0, tk.END)
        
        try:
            # Parse trading bot log to count filter blocks
            log_file = 'trading_bot.log'
            if not os.path.exists(log_file):
                self.filter_stats_text.insert(tk.END, f"Log file not found at {log_file}\n")
                return
            
            filter_counts = {
                'news': 0,
                'earnings': 0,
                'macro': 0,
                'sentiment': 0,
                'options': 0,
                'other': 0
            }
            
            # Read log and count filter blocks
            with open(log_file, 'r') as f:
                for line in f:
                    if 'FILTER - TRADE SKIPPED' in line or 'Filter alert' in line:
                        if 'NEWS FILTER' in line:
                            filter_counts['news'] += 1
                        elif 'EARNINGS FILTER' in line:
                            filter_counts['earnings'] += 1
                        elif 'MACRO FILTER' in line:
                            filter_counts['macro'] += 1
                        elif 'SENTIMENT FILTER' in line or 'FOMO FILTER' in line:
                            filter_counts['sentiment'] += 1
                        elif 'OPTIONS FILTER' in line:
                            filter_counts['options'] += 1
                        else:
                            filter_counts['other'] += 1
            
            # Calculate totals
            total_blocks = sum(filter_counts.values())
            
            self.filter_stats_text.insert(tk.END, f"FILTER EFFECTIVENESS ANALYSIS\n")
            self.filter_stats_text.insert(tk.END, "="*70 + "\n\n")
            self.filter_stats_text.insert(tk.END, f"Total Trades Blocked: {total_blocks}\n\n")
            
            if total_blocks > 0:
                self.filter_stats_text.insert(tk.END, "Block Breakdown:\n")
                self.filter_stats_text.insert(tk.END, "-"*70 + "\n\n")
                
                for filter_name in ['news', 'earnings', 'macro', 'sentiment', 'options']:
                    count = filter_counts[filter_name]
                    pct = (count / total_blocks * 100) if total_blocks > 0 else 0
                    emoji = {
                        'news': '📰',
                        'earnings': '📊',
                        'macro': '🏦',
                        'sentiment': '😱',
                        'options': '🎯'
                    }.get(filter_name, '⚪')
                    
                    bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
                    self.filter_stats_text.insert(tk.END, f"{emoji} {filter_name.capitalize():12} [{bar}] {count:3} ({pct:5.1f}%)\n")
                
                # Other filters
                if filter_counts['other'] > 0:
                    pct = (filter_counts['other'] / total_blocks * 100)
                    bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
                    self.filter_stats_text.insert(tk.END, f"⚪ Other        [{bar}] {filter_counts['other']:3} ({pct:5.1f}%)\n")
            else:
                self.filter_stats_text.insert(tk.END, "No filter blocks recorded yet\n")
        
        except Exception as e:
            self.filter_stats_text.insert(tk.END, f"Error analyzing filters: {e}\n")
    
    def refresh_stats(self):
        """Refresh statistics display"""
        if not self.bot:
            self.stats_text.insert(tk.END, "No bot instance running\n")
            return
        
        self.stats_text.delete(1.0, tk.END)
        
        stats = f"""
TRADING BOT STATISTICS
{'='*60}

Total Trades: {self.bot.track_record['total_trades']}
Winning Trades: {self.bot.track_record['winning_trades']}
Losing Trades: {self.bot.track_record['losing_trades']}
Win Rate: {self.bot.track_record['win_rate']*100:.1f}%
Consecutive Losses: {self.bot.consecutive_losses}

Current Allocation: ${self.bot.track_record['current_allocation']:.2f}
Total Capital: ${self.bot.total_capital:.2f}

Open Positions: {len(self.bot.positions)}
Max Positions: {self.max_positions_var.get()}

PDT Day Trades: {self.pdt_tracker.get_day_trade_count()}/3
PDT Capital: ${self.pdt_tracker.current_capital:.2f}
Capital Floor: ${self.pdt_tracker.capital_floor:.2f}

Mode: {'PAPER TRADING' if PAPER_TRADING_MODE else 'LIVE TRADING'}
{'='*60}
"""
        
        self.stats_text.insert(tk.END, stats)
    
    def show_about(self):
        """Show about dialog with disclaimer"""
        about_text = """Market Pie5 Trading Bot

Version 1.0
Automated trading bot with PDT compliance
and resource monitoring for Raspberry Pi 5

⚠️ DISCLAIMER - IMPORTANT
This is EXPERIMENTAL SOFTWARE for educational purposes only.

• Trading involves SIGNIFICANT RISK of financial loss
• The author is NOT RESPONSIBLE for any losses
• This software is provided "AS IS" without warranty
• You assume ALL RISKS when using this software
• USE AT YOUR OWN RISK

By using this software, you accept all risks and agree
to the full disclaimer in the README.

See: https://github.com/operator/market-pie5-bot
"""
        messagebox.showinfo("About Market Pie5 Bot", about_text)
    
    def show_pdt_info(self):
        """Show PDT rules information"""
        # Get starting capital from PDT tracker (reflects actual configured value)
        starting_capital = self.pdt_tracker.starting_capital
        capital_floor = self.pdt_tracker.capital_floor
        
        pdt_info = f"""
Pattern Day Trading (PDT) Rules

The PDT rule applies to traders with less than $25,000 in their account.

Key Points:
• A day trade is buying and selling the same stock on the same day
• More than 3 day trades within 5 business days triggers PDT status
• Accounts under $25,000 are limited to 3 day trades per 5 business days
• Violating this rule can result in account restrictions

This bot automatically tracks your day trades and prevents violations
when PDT protection is enabled.

Starting Capital: ${starting_capital:.2f}
Capital Floor: 10% (${capital_floor:.2f}) - Bot pauses if capital drops below this level
"""
        messagebox.showinfo("PDT Rules", pdt_info)


def main():
    """Main entry point for GUI application"""
    # Check if tkinter is available
    if not TKINTER_AVAILABLE:
        sys.stderr.write(_tkinter_error_message)
        sys.exit(1)
    
    root = tk.Tk()
    root.withdraw()  # Hide main window temporarily
    
    # Show disclaimer on startup
    disclaimer_text = """⚠️ IMPORTANT DISCLAIMER - READ CAREFULLY

This is EXPERIMENTAL SOFTWARE for educational purposes only.

• Trading involves SIGNIFICANT RISK of financial loss
• The author is NOT RESPONSIBLE for any losses
• This software is provided "AS IS" without warranty
• You assume ALL RISKS when using this software

By clicking "I Understand", you accept all risks and agree
to the full disclaimer in the README.

For complete terms, see:
https://github.com/operator/market-pie5-bot

Do you understand and accept these terms?"""
    
    # Show disclaimer and wait for response
    result = messagebox.askokcancel(
        "⚠️ DISCLAIMER - Use At Your Own Risk", 
        disclaimer_text,
        icon='warning'
    )
    
    if not result:
        # User clicked Cancel or closed the dialog
        root.destroy()
        return
    
    # User accepted, show main window
    root.deiconify()
    app = TradingBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
