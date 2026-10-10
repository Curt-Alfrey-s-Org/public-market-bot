#!/usr/bin/env python3
"""
Error Log Collection Script for market-pie5-bot
Collects all logs, selftest results, debug logs, and errors into errorlogs.txt
for analysis by GitHub Copilot.
"""

import os
import sys
import json
import glob
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class ErrorLogCollector:
    """Collects all logs and error information into a single file"""
    
    def __init__(self, output_file: str = "errorlogs.txt"):
        self.output_file = output_file
        self.project_root = Path(__file__).parent.resolve()
        self.sections: List[Dict[str, Any]] = []
        
    def add_section(self, title: str, content: str, source: str = ""):
        """Add a section to the error log"""
        self.sections.append({
            'title': title,
            'content': content,
            'source': source,
            'timestamp': datetime.now().isoformat()
        })
    
    def collect_file_contents(self, file_path: Path, title: str = None, 
                             max_lines: int = None) -> bool:
        """
        Collect contents from a file
        
        Args:
            file_path: Path to the file
            title: Optional title (defaults to filename)
            max_lines: Optional limit on number of lines
            
        Returns:
            True if file was collected, False otherwise
        """
        try:
            if not file_path.exists():
                return False
            
            if title is None:
                title = f"File: {file_path.name}"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"\n... (truncated after {max_lines} lines)")
                            break
                        lines.append(line.rstrip())
                    content = '\n'.join(lines)
                else:
                    content = f.read()
            
            file_size = file_path.stat().st_size
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            header = f"Source: {file_path}\n"
            header += f"Size: {file_size} bytes\n"
            header += f"Modified: {file_mtime.isoformat()}\n"
            header += "=" * 80 + "\n"
            
            self.add_section(title, header + content, str(file_path))
            return True
            
        except Exception as e:
            self.add_section(
                f"ERROR collecting {file_path}",
                f"Failed to collect: {str(e)}\n{traceback.format_exc()}",
                str(file_path)
            )
            return False
    
    def collect_directory_files(self, directory: Path, pattern: str = "*", 
                               title_prefix: str = "", max_files: int = 100):
        """Collect all files matching pattern in directory"""
        if not directory.exists():
            return
        
        files = sorted(directory.glob(pattern))[:max_files]
        for file_path in files:
            if file_path.is_file():
                title = f"{title_prefix}{file_path.name}" if title_prefix else None
                self.collect_file_contents(file_path, title)
    
    def collect_recent_files(self, pattern: str, title_prefix: str = "", 
                           max_files: int = 5):
        """Collect most recent files matching a glob pattern"""
        files = glob.glob(str(self.project_root / pattern))
        if not files:
            return
        
        # Sort by modification time, most recent first
        files_sorted = sorted(files, key=lambda x: os.path.getmtime(x), reverse=True)
        
        for file_path in files_sorted[:max_files]:
            path = Path(file_path)
            if path.is_file():
                title = f"{title_prefix}{path.name}" if title_prefix else None
                self.collect_file_contents(path, title)
    
    def collect_json_file(self, file_path: Path, title: str = None):
        """Collect and format JSON file"""
        try:
            if not file_path.exists():
                return False
            
            if title is None:
                title = f"JSON: {file_path.name}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Pretty print JSON
            content = json.dumps(data, indent=2, default=str)
            
            header = f"Source: {file_path}\n"
            header += "=" * 80 + "\n"
            
            self.add_section(title, header + content, str(file_path))
            return True
            
        except Exception as e:
            self.add_section(
                f"ERROR parsing JSON {file_path}",
                f"Failed to parse: {str(e)}\n{traceback.format_exc()}",
                str(file_path)
            )
            return False
    
    def collect_environment_info(self):
        """Collect environment and system information"""
        info = []
        info.append("=" * 80)
        info.append("ENVIRONMENT INFORMATION")
        info.append("=" * 80)
        info.append(f"Timestamp: {datetime.now().isoformat()}")
        info.append(f"Python Version: {sys.version}")
        info.append(f"Python Executable: {sys.executable}")
        info.append(f"Working Directory: {os.getcwd()}")
        info.append(f"Project Root: {self.project_root}")
        info.append("")
        
        # Environment variables (sanitized)
        info.append("Environment Variables (sanitized):")
        sensitive_keys = ['PASSWORD', 'SECRET', 'TOKEN', 'KEY', 'API_KEY', 
                         'APP_SECRET', 'ENCRYPTION_KEY']
        for key, value in sorted(os.environ.items()):
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                info.append(f"  {key}=***REDACTED***")
            else:
                info.append(f"  {key}={value}")
        
        self.add_section("Environment Information", '\n'.join(info), "system")
    
    def collect_all_logs(self):
        """Main collection routine"""
        print("Collecting error logs and debug information...")
        print("=" * 80)
        
        # 1. Environment information
        print("1. Collecting environment information...")
        self.collect_environment_info()
        
        # 2. Application logs (root directory)
        print("2. Collecting application logs...")
        log_files = list(self.project_root.glob("*.log"))
        if log_files:
            print(f"   Found {len(log_files)} log files in root")
            for log_file in log_files:
                self.collect_file_contents(log_file, f"App Log: {log_file.name}")
        else:
            print("   No log files found in root directory")
        
        # 3. API logs from /tmp
        print("3. Collecting API logs...")
        api_log = Path("/tmp/market-bot-api.log")
        if api_log.exists():
            print(f"   Found API log: {api_log}")
            # Only collect last 1000 lines to avoid huge files
            self.collect_file_contents(api_log, "API Log", max_lines=1000)
        else:
            print("   No API log found at /tmp/market-bot-api.log")
        
        # 4. Debug logs directory
        print("4. Collecting debug logs...")
        debug_dir = self.project_root / "debug_logs"
        if debug_dir.exists():
            debug_files = list(debug_dir.glob("*"))
            print(f"   Found {len(debug_files)} files in debug_logs/")
            self.collect_directory_files(debug_dir, "*", "Debug Log: ", max_files=50)
        else:
            print("   No debug_logs/ directory found")
        
        # 5. Logs directory (LogManager, CopilotDebugLogger)
        print("5. Collecting logs directory...")
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*"))
            print(f"   Found {len(log_files)} files in logs/")
            self.collect_directory_files(logs_dir, "*.json", "Trade Log: ", max_files=50)
            self.collect_directory_files(logs_dir, "*.jsonl", "Debug Log: ", max_files=50)
            self.collect_directory_files(logs_dir, "*.txt", "Text Log: ", max_files=50)
        else:
            print("   No logs/ directory found")
        
        # 6. Test results
        print("6. Collecting test results...")
        self.collect_recent_files("test_report_*.json", "Test Report: ", max_files=3)
        self.collect_file_contents(self.project_root / "test_results.txt", "Test Results Summary")
        self.collect_file_contents(self.project_root / "test_failures.txt", "Test Failures")
        
        # 7. Self-test results
        print("7. Collecting self-test results...")
        self.collect_file_contents(self.project_root / "selftest_debug.log", "Self-Test Debug Log")
        
        # 8. Error files
        print("8. Collecting error files...")
        self.collect_file_contents(self.project_root / "errors-i-found.txt", "Known Errors")
        
        # 9. Backtesting reports
        print("9. Collecting recent backtest reports...")
        self.collect_recent_files("backtest_report*.json", "Backtest Report: ", max_files=2)
        
        # 10. ML optimization reports
        print("10. Collecting ML optimization reports...")
        self.collect_recent_files("ml_optimization_*.json", "ML Optimization: ", max_files=2)
        
        # 11. Stock screener results
        print("11. Collecting stock screener results...")
        self.collect_file_contents(self.project_root / "screener_results.txt", "Stock Screener Results")
        
        # 12. Git status (helpful for context)
        print("12. Collecting git status...")
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info = "Git Status:\n" + result.stdout
                result_branch = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result_branch.returncode == 0:
                    git_info = f"Current Branch: {result_branch.stdout.strip()}\n\n" + git_info
                self.add_section("Git Status", git_info, "git")
        except Exception as e:
            print(f"   Could not collect git status: {e}")
        
        print("=" * 80)
        print(f"Collection complete: {len(self.sections)} sections collected")
    
    def write_output(self):
        """Write all collected logs to output file"""
        output_path = self.project_root / self.output_file
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("ERROR LOGS AND DEBUG INFORMATION\n")
                f.write("Collected by collect_errorlogs.py\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Total Sections: {len(self.sections)}\n\n")
                
                # Write table of contents
                f.write("=" * 80 + "\n")
                f.write("TABLE OF CONTENTS\n")
                f.write("=" * 80 + "\n")
                for i, section in enumerate(self.sections, 1):
                    f.write(f"{i}. {section['title']}\n")
                    if section['source']:
                        f.write(f"   Source: {section['source']}\n")
                f.write("\n\n")
                
                # Write all sections
                for i, section in enumerate(self.sections, 1):
                    f.write("\n" + "=" * 80 + "\n")
                    f.write(f"SECTION {i}: {section['title']}\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Timestamp: {section['timestamp']}\n")
                    if section['source']:
                        f.write(f"Source: {section['source']}\n")
                    f.write("-" * 80 + "\n")
                    f.write(section['content'])
                    f.write("\n\n")
            
            print(f"\n✓ Error logs written to: {output_path}")
            print(f"  File size: {output_path.stat().st_size:,} bytes")
            return True
            
        except Exception as e:
            print(f"\n✗ Failed to write output file: {e}")
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    print("=" * 80)
    print("ERROR LOG COLLECTOR")
    print("Collecting all logs, selftest results, and debug information")
    print("=" * 80)
    print()
    
    # Allow custom output filename
    output_file = sys.argv[1] if len(sys.argv) > 1 else "errorlogs.txt"
    
    collector = ErrorLogCollector(output_file)
    
    try:
        collector.collect_all_logs()
        success = collector.write_output()
        
        if success:
            print("\n✓ Success! Error logs collected.")
            print(f"\nTo analyze the logs, you can:")
            print(f"  1. Open {output_file} in your editor")
            print(f"  2. Search for 'ERROR', 'CRITICAL', 'FAIL', 'Exception'")
            print(f"  3. Review the Table of Contents for specific sections")
            print(f"\nTo push to remote for Copilot analysis:")
            print(f"  git add {output_file}")
            print(f"  git commit -m 'Add error logs for analysis'")
            print(f"  git push")
            return 0
        else:
            print("\n✗ Failed to collect logs")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nCollection interrupted by user")
        return 130
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
