# Security Policy

## Overview

The security of **market-pie5-bot** and your trading data is our top priority. This document outlines our security policies, vulnerability reporting procedures, and best practices for secure deployment.

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          | Notes                           |
| ------- | ------------------ | ------------------------------- |
| Latest (main) | :white_check_mark: | Active development, security fixes applied immediately |
| develop | :white_check_mark: | Pre-release testing branch |
| < 1.0   | :x:                | Legacy versions, no longer maintained |

**Recommendation:** Always use the latest version from the `main` branch for production deployments.

## Reporting a Vulnerability

If you discover a security vulnerability in market-pie5-bot, please report it responsibly:

### Reporting Process

1. **DO NOT** open a public GitHub issue for security vulnerabilities
2. **Email** the maintainer directly at the email associated with the repository owner's GitHub account
3. **Include** the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Suggested fix (if applicable)
   - Your contact information for follow-up

### What to Expect

- **Acknowledgment:** We will acknowledge receipt of your report within 48 hours
- **Assessment:** We will assess the vulnerability and determine its severity within 5 business days
- **Fix Timeline:**
  - **Critical vulnerabilities:** Patch within 7 days
  - **High severity:** Patch within 14 days
  - **Medium/Low severity:** Patch in next regular release
- **Disclosure:** We will coordinate disclosure with you after a fix is available
- **Credit:** You will be credited in the CHANGELOG.md (unless you prefer to remain anonymous)

## Security Features

### 1. Credential Protection

**Token Encryption:**
- OAuth tokens are encrypted using Fernet symmetric encryption (AES-128)
- HMAC-SHA256 integrity verification prevents tampering
- Encryption keys stored separately from tokens
- See [TOKEN_ENCRYPTION_GUIDE.md](TOKEN_ENCRYPTION_GUIDE.md) for setup

**Environment Variable Security:**
- All sensitive credentials stored in `.env` (never committed)
- `.env.example` provides template without real values
- `.gitignore` configured to exclude all credential files
- Support for encrypted environment variables

**Excluded from Version Control:**
```
.env                    # API keys and configuration
token.json             # OAuth tokens
.env.key, .token.key   # Encryption keys
```

### 2. API Security

**Schwab API Integration:**
- OAuth 2.0 authentication flow
- Token refresh handled automatically
- Direct API calls via `schwab-py` (no third-party intermediaries)
- Sandbox mode for safe testing

**API Key Validation:**
- Placeholder detection prevents accidental use of example credentials
- Live mode requires valid credentials (enforced)
- Paper mode can operate without real API keys

**Rate Limiting:**
- Respects API provider rate limits
- Configurable trading frequency (`TRADING_FREQUENCY`)
- Automatic backoff on API errors

### 3. Trading Safety

**Pattern Day Trading (PDT) Compliance:**
- Automatically enforced in live mode for accounts under $25,000
- Prevents regulatory violations
- Cannot be disabled in production mode

**Capital Floor Protection:**
- Bot pauses when capital drops below 10% of starting value
- Prevents catastrophic losses
- Configurable via `CAPITAL_FLOOR_PERCENT`

**Risk Management:**
- Default risk threshold: 2% per trade
- Trailing stop losses to limit downside
- Position size limits
- Maximum consecutive loss limits

**Mode Isolation:**
- Paper trading mode uses separate trade history files
- Sandbox mode isolated from production
- Dry-run mode for testing without execution
- Clear indicators of current mode in UI

### 4. Data Privacy

**Local Data Storage:**
- All trading data stored locally (no cloud uploads)
- Trade history in JSON files on your system
- Logs stored locally with sensitive data masked

**Third-Party Services:**
- HuggingFace API: Only sends aggregated statistics (no personal data)
- Yahoo Finance: Public data queries only (no authentication)
- Schwab API: Direct connection to regulated financial institution
- See [DATA_PRIVACY.md](DATA_PRIVACY.md) for complete details

**Log Security:**
- Sensitive data (tokens, API keys) automatically masked in logs
- Log rotation to prevent disk space exhaustion
- Configurable log levels

### 5. System Security

**ClamAV Antivirus Protection (Optional):**
- Virus and malware detection for system-wide protection
- Automatic virus definition updates via freshclam daemon
- Updates run hourly in the background
- Can be installed during setup with `./install.sh`
- Manual installation: `sudo apt install clamav clamav-daemon clamav-freshclam`
- Scan files/directories: `clamscan -r /path/to/directory`
- Check update status: `sudo systemctl status clamav-freshclam`

**System Isolation:**
- Bot runs in Python virtual environment (venv)
- Isolated dependencies prevent system-wide conflicts
- No sudo/root required for bot operation
- User-level permissions only

### 6. Code Security

**Automated Security Scanning:**
- **CodeQL:** Advanced semantic code analysis for vulnerabilities
- **Bandit:** Python-specific security issue detection
- **Safety:** Dependency vulnerability scanning
- Runs automatically on every push and weekly

**Dependency Management:**
- Regular dependency updates
- Automated vulnerability notifications
- Minimal dependency footprint to reduce attack surface

**Input Validation:**
- All user inputs validated before processing
- Type checking on critical functions
- Bounds checking on numerical inputs

## Security Best Practices

### For Developers

1. **Never commit secrets:**
   - Always use `.env` for sensitive data
   - Review changes before committing: `git diff`
   - Use `git-secrets` or similar tools to prevent accidental commits

2. **Keep dependencies updated:**
   ```bash
   pip list --outdated
   pip install --upgrade -r requirements.txt
   ```

3. **Run security scans locally:**
   ```bash
   # Check for dependency vulnerabilities
   pip install safety
   safety check -r requirements.txt
   
   # Check for code security issues
   pip install bandit
   bandit -r . -x ./venv,./test_*.py
   ```

4. **Review security test results:**
   ```bash
   # Run security-specific tests
   python -m unittest test_security_validation -v
   python -m unittest test_token_security -v
   ```

### For Users/Traders

1. **Start with paper trading:**
   ```bash
   # Set in .env
   PAPER_TRADING_MODE=true
   SCHWAB_SANDBOX_MODE=true
   ```

2. **Use token encryption:**
   ```bash
   # Generate encryption key
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   
   # Add to .env
   SCHWAB_TOKEN_ENCRYPTION_KEY=your_key_here
   SCHWAB_ENCRYPT_TOKEN=true
   ```

3. **Protect your environment file:**
   ```bash
   chmod 600 .env              # Read/write for owner only
   chmod 600 token.json        # Protect OAuth tokens
   chmod 600 .token.key        # Protect encryption key
   ```

4. **Regular backups:**
   - Back up `.env` and encryption keys securely
   - Use encrypted storage for backups
   - Store backups separately from application

5. **Monitor logs for unusual activity:**
   ```bash
   tail -f logs/trading_bot.log
   grep -i "error\|fail\|unauthorized" logs/*.log
   ```

6. **Use strong API credentials:**
   - Use Schwab's multi-factor authentication
   - Rotate API keys periodically
   - Use separate accounts for testing vs. production

7. **Network security:**
   - Run on trusted networks only
   - Use firewall to restrict unnecessary access
   - Consider VPN for remote access to web GUI

8. **System updates:**
   ```bash
   # Keep Raspberry Pi OS updated
   sudo apt update && sudo apt upgrade
   
   # Keep Python packages updated
   pip install --upgrade pip
   pip install --upgrade -r requirements.txt
   ```

## Known Security Considerations

### High-Risk Scenarios

1. **Live Trading Mode:**
   - Uses real money and real API credentials
   - Always test thoroughly in paper/sandbox mode first
   - Start with small position sizes
   - Monitor actively during initial live trading sessions

2. **Unencrypted Tokens:**
   - If `SCHWAB_ENCRYPT_TOKEN=false`, tokens stored in plaintext
   - Risk of credential theft if system is compromised
   - **Recommendation:** Always enable encryption in production

3. **Web GUI Remote Access:**
   - Default configuration binds to `localhost` only
   - Exposing to network requires additional security measures
   - **Recommendation:** Use SSH tunneling or VPN for remote access

4. **API Key Exposure:**
   - Environment variables visible to all processes on system
   - **Mitigation:** Run on dedicated system or user account
   - **Mitigation:** Use file-based encryption keys instead of env vars

### Medium-Risk Scenarios

1. **Dependency Vulnerabilities:**
   - Third-party packages may have undiscovered vulnerabilities
   - **Mitigation:** Automated scanning with Safety and CodeQL
   - **Mitigation:** Regular updates via `pip install --upgrade`

2. **Log File Exposure:**
   - Logs may contain transaction details
   - **Mitigation:** Sensitive data masked automatically
   - **Mitigation:** Restrict file permissions: `chmod 600 logs/*.log`

3. **Session Hijacking (Web GUI):**
   - Web GUI uses browser session
   - **Mitigation:** Runs on localhost by default
   - **Mitigation:** Implement authentication if exposing to network

## Security Workflow

Our automated security scanning runs:

- **On every push** to main and develop branches
- **On every pull request**
- **Weekly** on Sunday at 00:00 UTC (scheduled scan)

### CI/CD Security Checks

1. **CodeQL Analysis:**
   - Semantic code analysis for security vulnerabilities
   - Queries: `security-and-quality`
   - Results published to Security tab

2. **Dependency Scanning:**
   - `safety check` against known vulnerability database
   - Generates JSON report
   - Uploaded as build artifact

3. **Static Analysis:**
   - `bandit` security linter for Python
   - Checks for common security issues
   - Generates JSON report

### Viewing Security Results

1. **GitHub Security Tab:**
   - Navigate to repository → Security → Code scanning alerts
   - View CodeQL findings and severity

2. **GitHub Actions:**
   - Navigate to Actions → Security Scan workflow
   - Download security report artifacts
   - View detailed logs

3. **Local Testing:**
   ```bash
   # Run security workflow locally
   pip install safety bandit
   safety check -r requirements.txt
   bandit -r . -x ./venv,./test_*.py
   ```

## Security Roadmap

### Planned Enhancements

- [ ] Web GUI authentication/authorization system
- [ ] Rate limiting for API endpoints
- [ ] Automated dependency update PRs (Dependabot)
- [ ] Security advisory database integration
- [ ] Enhanced audit logging
- [ ] Two-factor authentication for web GUI
- [ ] API key rotation automation
- [ ] Secure credential storage service integration

### Recently Completed

- [x] Token encryption with Fernet
- [x] HMAC integrity verification
- [x] Log masking for sensitive data
- [x] Automated CodeQL scanning
- [x] Dependency vulnerability scanning
- [x] Placeholder credential detection
- [x] Mode-specific validation
- [x] Capital floor protection
- [x] PDT enforcement in live mode

## Compliance

### Financial Regulations

- **PDT Rule Compliance:** Pattern Day Trading rules enforced for U.S. accounts under $25,000
- **Broker Authorization:** Requires valid Schwab API credentials and account authorization
- **Audit Trail:** All trades logged with timestamps for compliance review

### Data Protection

- **No PII Collection:** Bot does not collect or transmit personally identifiable information
- **Local Storage:** All data stored locally on user's system
- **Data Retention:** User controls all data; no third-party storage
- **Right to Deletion:** Simply delete local files to remove all data

## Resources

### Documentation

- [TOKEN_ENCRYPTION_GUIDE.md](TOKEN_ENCRYPTION_GUIDE.md) - Encryption setup
- [DATA_PRIVACY.md](DATA_PRIVACY.md) - Privacy and third-party services
- [LIVE_MODE_GUIDE.md](LIVE_MODE_GUIDE.md) - Production deployment
- [CONTRIBUTING.md](CONTRIBUTING.md) - Security in development

### External References

- [Schwab API Documentation](https://developer.schwab.com)
- [OWASP Python Security](https://owasp.org/
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Python Security Best Practices](https://python.readthedocs.io/

## Contact

For security-related questions or concerns:

- **General Security Questions:** Open a GitHub discussion
- **Security Vulnerabilities:** Email repository owner (do not open public issue)
- **Security Advisory Notifications:** Watch the repository for security advisories

---

**Last Updated:** January 2026

**Version:** 1.0

This security policy is regularly reviewed and updated to address new threats and incorporate security improvements.
