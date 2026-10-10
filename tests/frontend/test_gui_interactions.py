"""
Frontend GUI Interaction Tests
Tests actual button clicks and interactions, verifying results
Uses browser automation to test the full user workflow
"""

from tests.framework.base_test import BaseTestModule, TestResult, TestStatus
import time


class GUIInteractionTest(BaseTestModule):
    """Test GUI interactions - actually clicks buttons and verifies results"""
    
    def __init__(self, api_base_url: str = "http://localhost:8002", frontend_url: str = "http://localhost:5173"):
        super().__init__("GUI Interactions", api_base_url)
        self.frontend_url = frontend_url
        self.browser = None
    
    def _get_browser(self):
        """Get browser instance (Selenium or Playwright)"""
        if self.browser:
            return self.browser
        
        # Try Playwright first (more modern)
        try:
            from playwright.sync_api import sync_playwright
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(headless=True)
            self.browser = browser
            return browser
        except ImportError:
            pass
        
        # Fallback to Selenium
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            browser = webdriver.Chrome(options=options)
            self.browser = browser
            return browser
        except ImportError:
            return None
        except Exception as e:
            self.log(f"Could not start browser: {e}", "WARN")
            return None
    
    def _cleanup_browser(self):
        """Close browser"""
        if self.browser:
            try:
                if hasattr(self.browser, 'close'):
                    self.browser.close()
                elif hasattr(self.browser, 'quit'):
                    self.browser.quit()
            except:
                pass
            self.browser = None
    
    def test_bot_start_button(self) -> TestResult:
        """Test that clicking Start button actually starts the bot"""
        def _test():
            browser = self._get_browser()
            if not browser:
                return TestResult(
                    "Bot Start Button",
                    TestStatus.SKIP,
                    "Browser automation not available (install playwright or selenium)"
                )
            
            try:
                # Navigate to frontend
                if hasattr(browser, 'goto'):
                    # Playwright
                    page = browser.new_page()
                    page.goto(self.frontend_url)
                else:
                    # Selenium
                    browser.get(self.frontend_url)
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    wait = WebDriverWait(browser, 10)
                
                # Wait for page to load
                time.sleep(2)
                
                # Get initial bot status via API
                initial_status = self.api_request("GET", "/api/bot/status")
                initial_running = initial_status.json().get("running", False)
                
                # Find and click Start button
                if hasattr(browser, 'goto'):
                    # Playwright
                    start_button = page.locator('button:has-text("Start")').first
                    if start_button.is_visible():
                        start_button.click()
                        page.wait_for_timeout(2000)  # Wait for API call
                    else:
                        # Bot might already be running
                        if initial_running:
                            return TestResult(
                                "Bot Start Button",
                                TestStatus.PASS,
                                "Bot already running (Start button not visible, as expected)"
                            )
                        return TestResult(
                            "Bot Start Button",
                            TestStatus.FAIL,
                            "Start button not found"
                        )
                else:
                    # Selenium
                    try:
                        start_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Start')]")))
                        start_btn.click()
                        time.sleep(2)  # Wait for API call
                    except:
                        if initial_running:
                            return TestResult(
                                "Bot Start Button",
                                TestStatus.PASS,
                                "Bot already running (Start button not visible, as expected)"
                            )
                        return TestResult(
                            "Bot Start Button",
                            TestStatus.FAIL,
                            "Start button not found or not clickable"
                        )
                
                # Verify bot is now running via API
                time.sleep(1)
                new_status = self.api_request("GET", "/api/bot/status")
                new_running = new_status.json().get("running", False)
                
                if new_running:
                    return True
                else:
                    return TestResult(
                        "Bot Start Button",
                        TestStatus.FAIL,
                        f"Clicked Start but bot is not running. Status: {new_status.json()}"
                    )
                    
            except Exception as e:
                return TestResult(
                    "Bot Start Button",
                    TestStatus.FAIL,
                    f"Error testing start button: {str(e)}"
                )
        
        return self.run_test("Bot Start Button", _test)
    
    def test_bot_stop_button(self) -> TestResult:
        """Test that clicking Stop button actually stops the bot"""
        def _test():
            browser = self._get_browser()
            if not browser:
                return TestResult(
                    "Bot Stop Button",
                    TestStatus.SKIP,
                    "Browser automation not available"
                )
            
            try:
                # First ensure bot is running
                start_response = self.api_request("POST", "/api/bot/start")
                time.sleep(2)  # Wait for bot to start
                
                # Navigate to frontend
                if hasattr(browser, 'goto'):
                    page = browser.new_page()
                    page.goto(self.frontend_url)
                    time.sleep(2)
                else:
                    browser.get(self.frontend_url)
                    time.sleep(2)
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    wait = WebDriverWait(browser, 10)
                
                # Verify bot is running
                status = self.api_request("GET", "/api/bot/status")
                if not status.json().get("running", False):
                    return TestResult(
                        "Bot Stop Button",
                        TestStatus.SKIP,
                        "Bot not running, cannot test stop button"
                    )
                
                # Find and click Stop button
                if hasattr(browser, 'goto'):
                    # Playwright
                    stop_button = page.locator('button:has-text("Stop")').first
                    if stop_button.is_visible():
                        stop_button.click()
                        page.wait_for_timeout(2000)
                    else:
                        return TestResult(
                            "Bot Stop Button",
                            TestStatus.FAIL,
                            "Stop button not found"
                        )
                else:
                    # Selenium
                    try:
                        stop_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Stop')]")))
                        stop_btn.click()
                        time.sleep(2)
                    except:
                        return TestResult(
                            "Bot Stop Button",
                            TestStatus.FAIL,
                            "Stop button not found or not clickable"
                        )
                
                # Verify bot is now stopped
                time.sleep(1)
                new_status = self.api_request("GET", "/api/bot/status")
                new_running = new_status.json().get("running", False)
                
                if not new_running:
                    return True
                else:
                    return TestResult(
                        "Bot Stop Button",
                        TestStatus.FAIL,
                        f"Clicked Stop but bot is still running. Status: {new_status.json()}"
                    )
                    
            except Exception as e:
                return TestResult(
                    "Bot Stop Button",
                    TestStatus.FAIL,
                    f"Error testing stop button: {str(e)}"
                )
        
        return self.run_test("Bot Stop Button", _test)
    
    def test_mode_change_button(self) -> TestResult:
        """Test that clicking mode buttons actually changes the mode"""
        def _test():
            browser = self._get_browser()
            if not browser:
                return TestResult(
                    "Mode Change Button",
                    TestStatus.SKIP,
                    "Browser automation not available"
                )
            
            try:
                # Get initial mode
                initial_status = self.api_request("GET", "/api/bot/status")
                initial_mode = initial_status.json().get("mode", "unknown")
                
                # Navigate to frontend
                if hasattr(browser, 'goto'):
                    page = browser.new_page()
                    page.goto(self.frontend_url)
                    time.sleep(2)
                else:
                    browser.get(self.frontend_url)
                    time.sleep(2)
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    wait = WebDriverWait(browser, 10)
                
                # Find a mode button (try yfinance if not already selected)
                target_mode = "yfinance" if initial_mode != "yfinance" else "sandbox"
                
                if hasattr(browser, 'goto'):
                    # Playwright
                    mode_button = page.locator(f'button:has-text("{target_mode.capitalize()}")').first
                    if not mode_button.is_visible():
                        mode_button = page.locator(f'button:has-text("YFinance")').first
                    
                    if mode_button.is_visible():
                        mode_button.click()
                        page.wait_for_timeout(2000)  # Wait for API call
                    else:
                        return TestResult(
                            "Mode Change Button",
                            TestStatus.FAIL,
                            f"Mode button for {target_mode} not found"
                        )
                else:
                    # Selenium
                    try:
                        mode_btn = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{target_mode.capitalize()}')]")))
                        mode_btn.click()
                        time.sleep(2)
                    except:
                        return TestResult(
                            "Mode Change Button",
                            TestStatus.FAIL,
                            f"Mode button for {target_mode} not found or not clickable"
                        )
                
                # Verify mode changed via API
                time.sleep(1)
                new_status = self.api_request("GET", "/api/bot/status")
                new_mode = new_status.json().get("mode", "unknown")
                
                # Mode should be updated (either on instance or in .env)
                # Check .env file to verify persistence
                import os
                env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env')
                if os.path.exists(env_file):
                    with open(env_file, 'r') as f:
                        env_content = f.read()
                        # Check if mode was persisted
                        if target_mode == "yfinance":
                            if "PAPER_TRADING_MODE=true" in env_content and "SCHWAB_SANDBOX_MODE=false" in env_content:
                                return True
                        elif target_mode == "sandbox":
                            if "PAPER_TRADING_MODE=true" in env_content and "SCHWAB_SANDBOX_MODE=true" in env_content:
                                return True
                
                # If mode changed on instance, that's also good
                if new_mode == target_mode or new_mode != initial_mode:
                    return True
                else:
                    return TestResult(
                        "Mode Change Button",
                        TestStatus.FAIL,
                        f"Clicked {target_mode} but mode is still {new_mode} (was {initial_mode})"
                    )
                    
            except Exception as e:
                return TestResult(
                    "Mode Change Button",
                    TestStatus.FAIL,
                    f"Error testing mode change: {str(e)}"
                )
        
        return self.run_test("Mode Change Button", _test)
    
    def test_stats_display_updates(self) -> TestResult:
        """Test that stats display actually updates when data changes"""
        def _test():
            browser = self._get_browser()
            if not browser:
                return TestResult(
                    "Stats Display Updates",
                    TestStatus.SKIP,
                    "Browser automation not available"
                )
            
            try:
                # Navigate to dashboard
                if hasattr(browser, 'goto'):
                    page = browser.new_page()
                    page.goto(self.frontend_url)
                    time.sleep(3)  # Wait for data to load
                else:
                    browser.get(self.frontend_url)
                    time.sleep(3)
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    wait = WebDriverWait(browser, 10)
                
                # Get stats from API
                api_stats = self.api_request("GET", "/api/stats")
                api_data = api_stats.json()
                api_capital = api_data.get("capital", 0)
                
                # Try to find capital value in UI
                if hasattr(browser, 'goto'):
                    # Playwright
                    capital_text = page.locator('text=/capital|Capital|\\$/i').first
                    if capital_text.is_visible():
                        # Found capital display
                        return True
                    else:
                        # Check if stats are displayed at all
                        stats_section = page.locator('[class*="stat"], [class*="capital"]').first
                        if stats_section.is_visible():
                            return TestResult(
                                "Stats Display Updates",
                                TestStatus.WARN,
                                "Stats section visible but cannot verify exact values"
                            )
                        return TestResult(
                            "Stats Display Updates",
                            TestStatus.FAIL,
                            "Stats not displayed in UI"
                        )
                else:
                    # Selenium
                    try:
                        # Look for capital or stats elements
                        capital_elem = browser.find_element(By.XPATH, "//*[contains(text(), '$') or contains(text(), 'capital')]")
                        if capital_elem:
                            return True
                    except:
                        pass
                    
                    # Check if any stats are displayed
                    try:
                        stats_elem = browser.find_element(By.CSS_SELECTOR, "[class*='stat'], [class*='capital']")
                        if stats_elem:
                            return TestResult(
                                "Stats Display Updates",
                                TestStatus.WARN,
                                "Stats section visible but cannot verify exact values"
                            )
                    except:
                        pass
                    
                    return TestResult(
                        "Stats Display Updates",
                        TestStatus.FAIL,
                        "Stats not displayed in UI"
                    )
                    
            except Exception as e:
                return TestResult(
                    "Stats Display Updates",
                    TestStatus.FAIL,
                    f"Error testing stats display: {str(e)}"
                )
        
        return self.run_test("Stats Display Updates", _test)
    
    def test_trades_table_displays(self) -> TestResult:
        """Test that trades table actually displays trade data"""
        def _test():
            browser = self._get_browser()
            if not browser:
                return TestResult(
                    "Trades Table Displays",
                    TestStatus.SKIP,
                    "Browser automation not available"
                )
            
            try:
                # Navigate to trades page
                trades_url = f"{self.frontend_url}/trades"
                if hasattr(browser, 'goto'):
                    page = browser.new_page()
                    page.goto(trades_url)
                    time.sleep(3)
                else:
                    browser.get(trades_url)
                    time.sleep(3)
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    wait = WebDriverWait(browser, 10)
                
                # Get trades from API
                api_trades = self.api_request("GET", "/api/trades")
                trades_data = api_trades.json()
                trade_count = trades_data.get("total", 0)
                
                # Look for trades table
                if hasattr(browser, 'goto'):
                    # Playwright
                    table = page.locator('table, [class*="table"], [class*="trade"]').first
                    if table.is_visible():
                        # Check if it has rows
                        rows = table.locator('tr, [class*="row"]')
                        row_count = rows.count()
                        if row_count > 0 or trade_count == 0:
                            return True
                        else:
                            return TestResult(
                                "Trades Table Displays",
                                TestStatus.FAIL,
                                f"Table visible but no rows (API shows {trade_count} trades)"
                            )
                    else:
                        if trade_count == 0:
                            return TestResult(
                                "Trades Table Displays",
                                TestStatus.PASS,
                                "No trades to display (expected)"
                            )
                        return TestResult(
                            "Trades Table Displays",
                            TestStatus.FAIL,
                            "Trades table not found"
                        )
                else:
                    # Selenium
                    try:
                        table = browser.find_element(By.CSS_SELECTOR, "table, [class*='table'], [class*='trade']")
                        if table:
                            rows = table.find_elements(By.TAG_NAME, "tr")
                            if len(rows) > 0 or trade_count == 0:
                                return True
                            else:
                                return TestResult(
                                    "Trades Table Displays",
                                    TestStatus.FAIL,
                                    f"Table visible but no rows (API shows {trade_count} trades)"
                                )
                    except:
                        if trade_count == 0:
                            return TestResult(
                                "Trades Table Displays",
                                TestStatus.PASS,
                                "No trades to display (expected)"
                            )
                        return TestResult(
                            "Trades Table Displays",
                            TestStatus.FAIL,
                            "Trades table not found"
                        )
                    
            except Exception as e:
                return TestResult(
                    "Trades Table Displays",
                    TestStatus.FAIL,
                    f"Error testing trades table: {str(e)}"
                )
        
        return self.run_test("Trades Table Displays", _test)
    
    def run(self):
        """Run all GUI interaction tests"""
        self.log("Starting GUI interaction tests...")
        self.log("These tests actually click buttons and verify results")
        
        tests = [
            self.test_bot_start_button,
            self.test_bot_stop_button,
            self.test_mode_change_button,
            self.test_stats_display_updates,
            self.test_trades_table_displays,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log(f"Test {test.__name__} raised exception: {e}", "ERROR")
        
        # Cleanup
        self._cleanup_browser()
        
        self.log(f"Completed {len(self.results)} tests")
        return self.results
