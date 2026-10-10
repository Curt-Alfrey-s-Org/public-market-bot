# Encryption Key Security Enhancements

## Overview

This document describes the security enhancements made to encryption key management in market-pie5-bot to address weak encryption key management vulnerabilities.

## Security Issues Addressed

### 1. Missing Permission Checks
**Previous Behavior:** When loading existing `.env.key` or `.token.key` files, the system did not verify file permissions. This meant insecure permissions (e.g., 0o644 - world readable) could exist without detection.

**New Behavior:** The system now:
- Checks file permissions before reading any key file
- Warns if permissions are not secure (0o600)
- Automatically attempts to fix insecure permissions
- Logs security warnings if permissions cannot be fixed

### 2. Silent Failures on Missing Keys
**Previous Behavior:** The `_get_token_encryption_key()` function returned `None` when no key was found, leading to silent failures during decryption attempts.

**New Behavior:** The system now:
- Automatically generates a new key if none exists
- Stores the generated key with secure permissions (0o600)
- Logs warnings when keys are generated
- Never returns `None` (except when cryptography library is unavailable)

### 3. No Key Rotation Support
**Previous Behavior:** There was no mechanism to rotate encryption keys for enhanced security.

**New Behavior:** The system now:
- Supports key rotation via the `MP5_ROTATE_ENCRYPTION_KEY` environment variable
- Automatically generates a new key when rotation is requested
- Clears the rotation flag after successful rotation
- Logs all key rotation events

## Features

### Automatic Permission Checking

When loading a key file, the system:

1. Checks if the file has secure permissions (0o600)
2. If permissions are insecure:
   - Logs a warning: `"Insecure permissions detected on .env.key - should be 0o600. Attempting to fix..."`
   - Attempts to fix permissions using `os.chmod(path, 0o600)`
   - Logs success or failure of the permission fix

Example warning in logs:
```
WARNING:schwab_auth:Insecure permissions detected on .env.key - should be 0o600. Attempting to fix...
INFO:schwab_auth:Fixed permissions for .env.key to 0o600
```

If the fix fails:
```
ERROR:schwab_auth:SECURITY WARNING: Could not fix permissions on .env.key - key file may be exposed!
```

### Automatic Key Generation

When no encryption key exists (neither in environment variables nor key files), the system:

1. Generates a new Fernet encryption key
2. Saves it to the appropriate file (`.env.key` or `.token.key`)
3. Sets secure permissions (0o600)
4. Logs a warning to alert the user

Example log message:
```
WARNING:schwab_auth:Generated new encryption key at .env.key - store securely!
```

### Key Rotation

To rotate an encryption key:

1. **Set the rotation flag:**
   ```bash
   export MP5_ROTATE_ENCRYPTION_KEY=true
   ```

2. **Run the bot** - the next time `_get_encryption_key()` is called:
   - A new key is generated
   - The old key file is overwritten
   - Secure permissions are set
   - The rotation flag is cleared

Example log output:
```
WARNING:schwab_auth:Key rotation requested via MP5_ROTATE_ENCRYPTION_KEY - generating new key
WARNING:schwab_auth:Generated new encryption key at .env.key - store securely!
```

**Important Notes:**
- Key rotation overwrites the existing key file
- Previously encrypted values will no longer be decryptable with the new key
- Back up your old key before rotation if you need to decrypt old values
- The rotation flag is automatically cleared after successful rotation

### Enhanced Token Key Management

The `_get_token_encryption_key()` function now:

1. Tries multiple key sources in priority order:
   - `SCHWAB_TOKEN_ENCRYPTION_KEY` environment variable
   - `MP5_ENCRYPTION_KEY` environment variable
   - `.token.key` file
   - `.env.key` file

2. Checks permissions on all key files before reading

3. Generates a new token key if none exists:
   ```
   WARNING:schwab_auth:No token encryption key found - generating new key
   WARNING:schwab_auth:Generated new token encryption key at .token.key - store securely!
   ```

4. Never returns `None` (unless cryptography is unavailable)

## Security Best Practices

### 1. File Permissions

Ensure all key files have secure permissions:

```bash
# Check permissions
ls -l .env.key .token.key

# Should show: -rw------- (0o600)
```

The system will attempt to fix insecure permissions automatically, but you should verify:

```bash
# Manually set secure permissions if needed
chmod 600 .env.key
chmod 600 .token.key
```

### 2. Environment Variables

Using environment variables is the most secure option:

```bash
# In .env file (never commit this file!)
MP5_ENCRYPTION_KEY=your_generated_key_here
SCHWAB_TOKEN_ENCRYPTION_KEY=your_generated_key_here
```

Generate keys:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Key Storage

- **Never commit** `.env.key`, `.token.key`, or `.env` files to version control
- Store keys in a secure password manager or secrets vault
- Use different keys for development and production
- Rotate keys periodically (e.g., every 90 days)

### 4. Key Rotation

Regular key rotation is a security best practice:

```bash
# 1. Back up current key (if needed to decrypt old data)
cp .env.key .env.key.backup

# 2. Rotate the key
export MP5_ROTATE_ENCRYPTION_KEY=true
./start_bot.sh  # or ./start_web_gui.sh

# 3. Update any external systems that use encrypted values
# 4. Securely delete the backup after migration
shred -u .env.key.backup  # Linux
# or
rm -P .env.key.backup  # macOS
```

### 5. Monitoring

Watch for security warnings in logs:

```bash
# Monitor for permission issues
tail -f bot.log | grep "SECURITY WARNING"

# Monitor for key generation events
tail -f bot.log | grep "Generated new encryption key"

# Monitor for key rotation events
tail -f bot.log | grep "Key rotation"
```

## Implementation Details

### Modified Functions

1. **`_check_file_permissions(file_path)`** (new)
   - Checks if a file has secure permissions (0o600)
   - Returns `True` if secure, `False` otherwise

2. **`_fix_file_permissions(file_path)`** (new)
   - Attempts to set file permissions to 0o600
   - Returns `True` on success, `False` on failure

3. **`_get_encryption_key()`** (enhanced)
   - Checks permissions before reading key files
   - Attempts to fix insecure permissions
   - Supports key rotation via environment variable
   - Always generates a key if none exists

4. **`_get_token_encryption_key()`** (enhanced)
   - Checks permissions on all key files
   - Generates a token key if none exists
   - Never returns `None` (unless cryptography unavailable)

### Files Modified

- `schwab_auth.py` - Enhanced both key functions
- `main.py` - Enhanced `_get_encryption_key()`
- `sentiment_analyzer.py` - Enhanced `_get_encryption_key()`
- `data_fetcher.py` - Enhanced `_get_encryption_key()`
- `web_gui.py` - Enhanced `_get_encryption_key()`

## Testing

### Automated Tests

Run the encryption security test suite:

```bash
python3 -m unittest test_encryption_security -v
```

Tests include:
- Permission detection and fixing
- Key rotation functionality
- Token key generation
- Secure permission verification
- Encryption/decryption with secure keys

### Manual Testing

1. **Test permission checking:**
   ```bash
   # Create key with insecure permissions
   python3 -c "from cryptography.fernet import Fernet; open('.env.key', 'wb').write(Fernet.generate_key())"
   chmod 644 .env.key
   
   # Start bot - should detect and fix permissions
   ./start_bot.sh
   
   # Verify permissions were fixed
   ls -l .env.key  # Should show -rw-------
   ```

2. **Test key rotation:**
   ```bash
   # Generate initial key
   python3 -c "from cryptography.fernet import Fernet; open('.env.key', 'wb').write(Fernet.generate_key())"
   OLD_KEY=$(cat .env.key | base64)
   
   # Rotate key
   export MP5_ROTATE_ENCRYPTION_KEY=true
   ./start_bot.sh
   
   # Verify key changed
   NEW_KEY=$(cat .env.key | base64)
   [ "$OLD_KEY" != "$NEW_KEY" ] && echo "✅ Key rotated successfully"
   ```

3. **Test token key generation:**
   ```bash
   # Remove all key files
   rm -f .env.key .token.key
   
   # Start bot - should generate token key
   ./start_bot.sh
   
   # Verify token key was created with secure permissions
   ls -l .token.key  # Should show -rw-------
   ```

## Troubleshooting

### Issue: "SECURITY WARNING: Could not fix permissions"

**Cause:** The system doesn't have permission to modify file permissions (e.g., key file owned by another user).

**Solution:**
```bash
# Take ownership of the file
sudo chown $USER:$USER .env.key

# Fix permissions manually
chmod 600 .env.key
```

### Issue: "No token encryption key found - generating new key" repeatedly

**Cause:** Key generation is failing silently, or key file is being deleted between runs.

**Solution:**
```bash
# Check if key file persists
ls -la .token.key .env.key

# Check file system permissions
ls -ld .

# Manually generate and verify key
python3 -c "from cryptography.fernet import Fernet; open('.token.key', 'wb').write(Fernet.generate_key())"
chmod 600 .token.key
```

### Issue: Key rotation not working

**Cause:** Environment variable not being passed to the process.

**Solution:**
```bash
# Use export to set environment variable
export MP5_ROTATE_ENCRYPTION_KEY=true

# Or set inline
MP5_ROTATE_ENCRYPTION_KEY=true ./start_bot.sh
```

## Migration Guide

### Upgrading from Previous Versions

If you're upgrading from a version without these security enhancements:

1. **Existing keys will be checked for permissions:**
   - If permissions are insecure, they will be automatically fixed
   - Watch logs for permission-related warnings

2. **No action required in most cases:**
   - The system is backward compatible
   - Existing key files continue to work
   - New security features activate automatically

3. **Recommended post-upgrade steps:**
   ```bash
   # Verify key file permissions
   ls -l .env.key .token.key
   
   # Should show: -rw------- (0o600)
   # If not, fix manually:
   chmod 600 .env.key .token.key
   
   # Consider rotating keys
   export MP5_ROTATE_ENCRYPTION_KEY=true
   ./start_bot.sh
   ```

## References

- [TOKEN_ENCRYPTION_GUIDE.md](TOKEN_ENCRYPTION_GUIDE.md) - General token encryption guide
- [test_encryption_security.py](test_encryption_security.py) - Security test suite
- [Fernet Symmetric Encryption](https://cryptography.io/en/latest/fernet/) - Cryptography library documentation

## Support

For security-related issues:
1. Check logs for specific error messages
2. Verify file permissions using `ls -l`
3. Test key generation manually
4. Review this guide's troubleshooting section
5. Open a GitHub issue with:
   - Sanitized log output (remove sensitive data)
   - Steps to reproduce
   - Expected vs. actual behavior
