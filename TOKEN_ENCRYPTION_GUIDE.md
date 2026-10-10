# Token Encryption Security Guide

## Overview

The Schwab authentication system now includes **token encryption** and **integrity checking** to enhance the security of your OAuth credentials. This guide explains how to set up and use these security features.

## Security Enhancements

### 1. Token Encryption (Fernet)
Your `token.json` file is encrypted using **Fernet symmetric encryption** (part of the `cryptography` library). This ensures that even if someone gains access to your file system, they cannot read your OAuth tokens without the encryption key.

### 2. HMAC Integrity Checking
Each encrypted token includes an **HMAC-SHA256** digest that verifies the file hasn't been corrupted or tampered with. The HMAC is computed on the encrypted data and verified **before decryption** for early detection of tampering. If the HMAC check fails, you'll be notified and required to re-authenticate.

### 3. Log Masking
Sensitive information like callback URLs and tokens are automatically masked in log files to prevent accidental exposure.

## Setup

### Quick Start (Recommended)

1. **Generate an encryption key:**
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Add to your `.env` file:**
   ```bash
   # Token Encryption Key
   SCHWAB_TOKEN_ENCRYPTION_KEY=your_generated_key_here
   ```

3. **Done!** Token encryption is enabled by default. Your next authentication will create an encrypted token.

### Alternative: Key File

Instead of an environment variable, you can store the key in a file:

```bash
# Generate key and save to file
python3 -c "from cryptography.fernet import Fernet; open('.token.key', 'wb').write(Fernet.generate_key())"
```

**Important:** Add `.token.key` to your `.gitignore` (already included) to prevent accidentally committing it.

### Key Priority Order

The system looks for encryption keys in this order:
1. `SCHWAB_TOKEN_ENCRYPTION_KEY` environment variable
2. `MP5_ENCRYPTION_KEY` environment variable (fallback)
3. `.token.key` file
4. `.env.key` file (fallback)

If no key is found, the token will be saved unencrypted (with a warning).

## Configuration Options

### Enable/Disable Encryption

Encryption is **enabled by default**. To disable it:

```bash
# In .env file
SCHWAB_ENCRYPT_TOKEN=false
```

**Note:** Disabling encryption is not recommended for production use.

### Environment Variables

```bash
# Token file location (default: token.json)
SCHWAB_TOKEN_PATH=token.json

# Enable token encryption (default: true)
SCHWAB_ENCRYPT_TOKEN=true

# Encryption key (generate with Fernet.generate_key())
SCHWAB_TOKEN_ENCRYPTION_KEY=your_key_here

# Alternative: General encryption key (used if SCHWAB_TOKEN_ENCRYPTION_KEY not set)
MP5_ENCRYPTION_KEY=your_key_here
```

## Migrating Existing Tokens

### From Plain to Encrypted

If you have an existing plain `token.json` file:

1. **Set up encryption key** (see Setup above)
2. **Run the bot** - it will detect the plain token and work normally
3. **Next token refresh** - the token will be automatically saved encrypted

The system maintains **backward compatibility** - plain tokens work with encryption enabled.

### Manual Migration

To immediately encrypt an existing plain token:

```python
from schwab_auth import SchwabAuthenticator
from cryptography.fernet import Fernet
import os

# Set up encryption key
os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = 'your_key_here'

# Create authenticator
auth = SchwabAuthenticator(
    api_key=os.getenv('SCHWAB_API_KEY'),
    app_secret=os.getenv('SCHWAB_APP_SECRET'),
    callback_url=os.getenv('SCHWAB_CALLBACK_URL'),
    token_path='token.json',
    encrypt_token=True
)

# Load plain token
token_data = auth._load_encrypted_token()

# Save as encrypted
auth._save_encrypted_token(token_data)

print("Token encrypted successfully!")
```

## Encrypted Token Format

An encrypted token file looks like this:

```json
{
  "encrypted": true,
  "hmac": "a1b2c3d4e5f6...",
  "data": "gAAAAABpbxRA..."
}
```

- `encrypted`: Flag indicating encryption is used
- `hmac`: HMAC-SHA256 digest for integrity verification
- `data`: Fernet-encrypted token data (Base64 encoded)

A plain token file looks like this:

```json
{
  "access_token": "change-me",
  "refresh_token": "change-me",
  "expires_at": 1234567890,
  ...
}
```

## Security Best Practices

### ✅ Do:

- **Store encryption key securely** - use environment variables or key files
- **Add `.token.key` and `.env.key` to `.gitignore`** (already done)
- **Use different keys for development and production**
- **Rotate keys periodically** (every 3-6 months)
- **Enable encryption in production** (enabled by default)
- **Back up your encryption key** securely (not in the repository)

### ❌ Don't:

- **Don't commit encryption keys to Git**
- **Don't share keys in plain text** (Slack, email, etc.)
- **Don't use the same key across multiple projects**
- **Don't disable encryption in production** without good reason
- **Don't ignore HMAC verification failures** - investigate them

## Troubleshooting

### Error: "Token file is encrypted but no encryption key found"

**Cause:** You have an encrypted token but the encryption key is missing.

**Solution:**
1. Set the encryption key environment variable:
   ```bash
   export SCHWAB_TOKEN_ENCRYPTION_KEY=your_key_here
   ```
2. Or create a `.token.key` file with the key
3. If you've lost the key, delete `token.json` and re-authenticate

### Error: "Token file integrity check failed (HMAC mismatch)"

**Cause:** The token file may be corrupted or tampered with.

**Solution:**
1. **Investigate** - this could indicate a security issue
2. **Delete the corrupted token:**
   ```bash
   rm token.json
   ```
3. **Re-authenticate:**
   ```bash
   python3 main.py
   ```

### Warning: "No encryption key found - saving token unencrypted"

**Cause:** Encryption is enabled but no key is available.

**Solution:**
1. Generate and set up an encryption key (see Setup above)
2. Or disable encryption explicitly:
   ```bash
   SCHWAB_ENCRYPT_TOKEN=false
   ```

### Token works but logs show "Token loaded (unencrypted)"

**Cause:** You have a plain token file with encryption enabled.

**Solution:** This is normal during migration. The token will be encrypted on the next refresh. To encrypt immediately, see "Manual Migration" above.

## CI/CD and Automation

### GitHub Actions / CI/CD

Store the encryption key as a **secret** in your CI/CD system:

**GitHub Actions:**
```yaml
jobs:
  test:
    steps:
      - name: Run tests
        env:
          SCHWAB_TOKEN_ENCRYPTION_KEY: ${{ secrets.SCHWAB_TOKEN_ENCRYPTION_KEY }}
        run: python3 main.py
```

**GitLab CI:**
```yaml
test:
  script:
    - python3 main.py
  variables:
    SCHWAB_TOKEN_ENCRYPTION_KEY: $SCHWAB_TOKEN_ENCRYPTION_KEY
```

### Docker

Pass the key as an environment variable:

```bash
docker run -e SCHWAB_TOKEN_ENCRYPTION_KEY=your_key_here ...
```

Or mount a key file:

```bash
docker run -v /secure/path/.token.key:/app/.token.key ...
```

## Key Rotation

To rotate your encryption key:

1. **Generate a new key:**
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Decrypt with old key and re-encrypt with new key:**
   ```python
   from schwab_auth import SchwabAuthenticator
   import os
   
   # Load with old key
   os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = 'old_key'
   auth_old = SchwabAuthenticator(..., encrypt_token=True)
   token_data = auth_old._load_encrypted_token()
   
   # Save with new key
   os.environ['SCHWAB_TOKEN_ENCRYPTION_KEY'] = 'new_key'
   auth_new = SchwabAuthenticator(..., encrypt_token=True)
   auth_new._save_encrypted_token(token_data)
   
   print("Key rotated successfully!")
   ```

3. **Update your `.env` file or key file** with the new key

4. **Update CI/CD secrets** if applicable

## Testing

Test your encryption setup:

```bash
# Run token security tests
python3 test_token_security.py

# Test your configuration
python3 -c "
from schwab_auth import _get_token_encryption_key
key = _get_token_encryption_key()
print('✓ Encryption key found' if key else '✗ No encryption key')
"
```

## FAQ

**Q: Is encryption required?**
A: No, but it's strongly recommended for production use. The bot will work without encryption.

**Q: What happens if I lose my encryption key?**
A: You'll need to delete `token.json` and re-authenticate. Your trading data is not affected.

**Q: Can I use the same key for multiple bots?**
A: While possible, it's better to use unique keys per bot for security isolation.

**Q: Does encryption slow down the bot?**
A: No, the performance impact is negligible (< 1ms per token operation).

**Q: What encryption algorithm is used?**
A: Fernet (AES-128 in CBC mode with HMAC-SHA256 for integrity).

**Q: Can I inspect an encrypted token?**
A: Only if you have the encryption key. Use the decryption methods in `schwab_auth.py`.

**Q: Does this encrypt API keys in `.env`?**
A: No, this feature only encrypts the OAuth token file. For encrypting environment variables, see the existing `MP5_ENCRYPTION_KEY` feature.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review logs for specific error messages
- Open an issue on GitHub with details

## Security Notice

**Report security vulnerabilities responsibly:**
- Do not open public GitHub issues for security problems
- Contact the maintainers directly
- Allow time for a fix before public disclosure

---

**Last Updated:** 2026-01-20
**Feature Version:** 1.0
**Compatible with:** market-pie5-bot v1.0+
