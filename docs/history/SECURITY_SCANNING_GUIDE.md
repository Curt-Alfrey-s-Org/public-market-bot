# Security Scanning and Alerts Guide

This guide explains how to view, understand, and respond to security scanning results in the market-pie5-bot repository.

## Overview

The repository uses multiple automated security scanning tools to detect vulnerabilities:

1. **CodeQL** - Advanced semantic code analysis
2. **Bandit** - Python-specific security linter
3. **Safety** - Dependency vulnerability scanner
4. **Dependabot** - Automated dependency updates and alerts

## Viewing Security Alerts

### GitHub Security Tab

1. Navigate to the repository on GitHub
2. Click the **Security** tab
3. View active alerts under:
   - **Code scanning alerts** (CodeQL findings)
   - **Dependabot alerts** (Dependency vulnerabilities)
   - **Secret scanning alerts** (If accidentally committed)

### Security Workflow Results

1. Go to **Actions** → **Security Scan** workflow
2. Click on the latest run
3. View the **Summary** tab for quick overview
4. Download **security-reports** artifact for detailed reports

## Understanding Severity Levels

### Critical/High Severity
- **Impact:** Could lead to unauthorized access, data loss, or system compromise
- **Action:** Fix immediately
- **Examples:** SQL injection, remote code execution, credential exposure

### Medium Severity
- **Impact:** Could be exploited under specific conditions
- **Action:** Fix in next maintenance cycle
- **Examples:** Information disclosure, weak encryption

### Low Severity
- **Impact:** Minimal risk, often requires specific circumstances
- **Action:** Fix when convenient
- **Examples:** Timing attacks, verbose error messages

## Common Security Issues

### 1. Pickle Deserialization (B301)

**Issue:** Using `pickle.load()` with untrusted data can be unsafe.

**Location:** `ml_signal_filter.py`, `stock_screener.py`

**Risk Level:** Medium (in this project, low risk since files are locally generated)

**Mitigation:**
- Files are created by the bot itself (trusted source)
- Not accepting pickle files from external sources
- Alternative: Use JSON for serialization (less efficient for ML models)

**Code example:**
```python
# Current (acceptable for local files)
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

# More secure alternative (for external files)
import joblib
model = joblib.load('model.pkl')  # Better security validation
```

### 2. Binding to All Interfaces (B104)

**Issue:** Web GUI binds to `0.0.0.0` (all network interfaces)

**Location:** `web_gui.py`

**Risk Level:** Medium (configurable risk)

**Mitigation:**
- Default localhost binding recommended for local use
- Use firewall rules if exposing to network
- Consider adding authentication for remote access
- Use SSH tunneling or VPN for secure remote access

**Code example:**
```python
# Current (allows network access)
app.run(host='0.0.0.0', port=8050)

# More secure (localhost only)
app.run(host='127.0.0.1', port=8050)
```

### 3. Dependency Vulnerabilities

**Issue:** Third-party packages may have known vulnerabilities

**Detection:** Safety check in CI/CD, Dependabot alerts

**Mitigation:**
- Update dependencies regularly: `pip install --upgrade -r requirements.txt`
- Review Dependabot PRs and merge security updates
- Pin versions to avoid unexpected updates in production

## Responding to Alerts

### Step 1: Assess the Alert

1. **Read the description** - Understand what the vulnerability is
2. **Check the severity** - Prioritize based on risk level
3. **Review the code** - Examine the flagged code in context
4. **Determine exploitability** - Can this be exploited in practice?

### Step 2: Decide on Action

- **Fix immediately:** Critical/high severity in production code
- **Schedule fix:** Medium severity or mitigated by other controls
- **Accept risk:** False positive or acceptable risk with justification
- **Suppress alert:** If fixing would break functionality (document why)

### Step 3: Implement Fix

1. Create a branch: `git checkout -b fix/security-issue-123`
2. Implement the fix
3. Test thoroughly: `pytest test_*.py -v`
4. Run security scan locally: `bandit -r . -ll -x ./venv,./test_*.py`
5. Commit and push: `git commit -m "Fix: Security issue #123"`
6. Create PR with security label

### Step 4: Verify Fix

1. Wait for CI/CD security scan to complete
2. Check that the alert is resolved
3. Download security reports to confirm
4. Update CHANGELOG.md with security fix note

## Running Security Scans Locally

### Full Security Scan

```bash
# Install tools
pip install safety bandit

# Check dependencies
pip install -r requirements.txt
safety check

# Scan code
bandit -r . -ll -x ./venv,./node_modules,./test_*.py
```

### Quick Security Check

```bash
# Check only high/medium severity issues
bandit -r . -ll -x ./venv,./test_*.py | grep -E "Severity: (High|Medium)"
```

### Scan Specific Files

```bash
# Scan a single file
bandit main.py

# Scan a directory
bandit -r web_gui.py strategies.py risk_management.py
```

## Security Best Practices

### For Developers

1. **Never commit secrets**
   ```bash
   # Check before committing
   git diff --cached
   grep -r "API_KEY\|SECRET\|PASSWORD" .
   ```

2. **Review dependencies before adding**
   ```bash
   # Check package info
   pip show package-name
   
   # Check for known vulnerabilities
   safety check --package package-name==version
   ```

3. **Use type hints and validation**
   ```python
   def execute_trade(symbol: str, amount: float) -> bool:
       if not isinstance(symbol, str) or not symbol.isalpha():
           raise ValueError("Invalid symbol")
       if amount <= 0:
           raise ValueError("Amount must be positive")
       # ... execute trade
   ```

4. **Sanitize user input**
   ```python
   import re
   
   # Validate stock symbols
   symbol = re.sub(r'[^A-Z]', '', symbol.upper())
   
   # Validate numeric input
   amount = max(0, min(amount, MAX_AMOUNT))
   ```

### For Users

1. **Keep software updated**
   ```bash
   git pull origin main
   pip install --upgrade -r requirements.txt
   ```

2. **Use encryption**
   ```bash
   # Enable token encryption in .env
   SCHWAB_ENCRYPT_TOKEN=true
   ```

3. **Restrict file permissions**
   ```bash
   chmod 600 .env token.json .token.key
   ```

4. **Monitor logs**
   ```bash
   tail -f logs/trading_bot.log
   grep -i "error\|unauthorized\|failed" logs/*.log
   ```

## Dependabot Configuration

Dependabot is configured to:
- Check for dependency updates **weekly** (Mondays at 9:00 AM)
- Create up to 5 PRs per ecosystem (Python, Node.js)
- Group related dependencies to reduce PR noise
- Label PRs with `dependencies` and `security`

### Reviewing Dependabot PRs

1. **Check the changelog** - Review what changed in the new version
2. **Review security advisories** - GitHub links to CVEs if applicable
3. **Test locally** - Pull the branch and run tests
4. **Merge promptly** - Security updates should be merged quickly

## Security Workflow Schedule

- **On every push:** Security scan runs automatically
- **On every PR:** Security scan validates changes
- **Weekly (Sundays):** Scheduled security scan
- **Weekly (Mondays):** Dependabot checks for updates

## Reporting Security Issues

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead, follow the process in [SECURITY.md](SECURITY.md):
1. Email the repository owner privately
2. Include vulnerability details and reproduction steps
3. Expect acknowledgment within 48 hours
4. Work with maintainers on responsible disclosure

## Resources

- [SECURITY.md](SECURITY.md) - Complete security policy
- [TOKEN_ENCRYPTION_GUIDE.md](TOKEN_ENCRYPTION_GUIDE.md) - Encryption setup
- [DATA_PRIVACY.md](DATA_PRIVACY.md) - Privacy information
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

## FAQ

### Q: Why do I see medium-severity pickle warnings?

A: The bot uses pickle for caching and ML model storage. This is safe because:
- Files are locally generated (trusted source)
- Not accepting pickle files from external sources
- Files are stored in restricted locations

### Q: Should I expose the web GUI to the network?

A: Only if necessary:
- For local use: Bind to `127.0.0.1` (localhost only)
- For network access: Use firewall rules and consider authentication
- For remote access: Use SSH tunneling or VPN

### Q: How do I know if my dependencies are secure?

A: Multiple checks:
1. Dependabot alerts in Security tab
2. Safety check in CI/CD
3. Run `safety check` locally
4. Review Dependabot PRs weekly

### Q: What should I do about low-severity issues?

A: Low-severity issues can be:
- Fixed when convenient (not urgent)
- Accepted if fixing would complicate code
- Documented with reasoning if left unfixed

### Q: How do I suppress false positives?

A: Add `# nosec` comment to the line:
```python
# This is safe because we only load locally generated files
model = pickle.load(f)  # nosec B301
```

Document why in code comments.

## Contact

- **Security Questions:** Open a GitHub discussion
- **Security Vulnerabilities:** Email repository owner (see SECURITY.md)
- **General Support:** GitHub issues
