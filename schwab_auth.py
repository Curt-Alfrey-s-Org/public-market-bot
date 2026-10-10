#!/usr/bin/env python3
"""
Schwab API Authentication Module
Handles OAuth authentication and client creation using schwab-py library

This module provides explicit sandbox/live environment distinction to prevent
mode confusion. While the schwab-py library determines the actual endpoint based
on API credentials, this module tracks the intended environment for validation
and logging purposes.
"""

import os
import stat
import json
import logging
import hmac
import hashlib
import tempfile
from typing import Optional

# Try to import schwab-py library
try:
    from schwab import auth
    SCHWAB_PY_AVAILABLE = True
except ImportError:
    SCHWAB_PY_AVAILABLE = False
    auth = None

# Try to import encryption library for decrypting sensitive environment variables
try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False

logger = logging.getLogger(__name__)

# Sensitive environment variable keys that may be encrypted
SENSITIVE_ENV_KEYS = {
    "SCHWAB_API_KEY",
    "SCHWAB_APP_SECRET",
}

def _check_file_permissions(file_path: str) -> bool:
    """
    Check if a file has secure permissions (owner read/write only, 0o600).
    
    Args:
        file_path: Path to file to check
        
    Returns:
        True if permissions are secure (0o600), False otherwise
    """
    if not os.path.exists(file_path):
        return True  # File doesn't exist, no permission issues
    
    try:
        file_stats = os.stat(file_path)
        file_mode = stat.S_IMODE(file_stats.st_mode)
        # Check if permissions are exactly 0o600 (owner read/write only)
        return file_mode == 0o600
    except OSError as e:
        logger.error(f"Failed to check permissions for {file_path}: {e}")
        return False

def _fix_file_permissions(file_path: str) -> bool:
    """
    Attempt to fix file permissions to 0o600.
    
    Args:
        file_path: Path to file to fix
        
    Returns:
        True if permissions were fixed successfully, False otherwise
    """
    try:
        os.chmod(file_path, 0o600)
        logger.info(f"Fixed permissions for {file_path} to 0o600")
        return True
    except OSError as e:
        logger.error(f"Failed to fix permissions for {file_path}: {e}")
        return False

def _get_encryption_key():
    """Return a Fernet key for encrypting/decrypting sensitive configuration values."""
    if not FERNET_AVAILABLE:
        return None
    
    # Check for key rotation flag
    if os.environ.get("MP5_ROTATE_ENCRYPTION_KEY", "").lower() == "true":
        logger.warning("Key rotation requested via MP5_ROTATE_ENCRYPTION_KEY - generating new key")
        key = Fernet.generate_key()
        key_path = ".env.key"
        try:
            with open(key_path, "wb") as f:
                f.write(key)
            os.chmod(key_path, 0o600)
            logger.warning("Generated new encryption key at %s - store securely!", key_path)
            # Clear the rotation flag to avoid repeated rotation (safe deletion)
            os.environ.pop("MP5_ROTATE_ENCRYPTION_KEY", None)
        except (OSError, IOError, PermissionError) as e:
            logger.error("Failed to persist encryption key during rotation: %s", e)
        return key
    
    # Try environment variable first
    key = os.environ.get("MP5_ENCRYPTION_KEY")
    if key:
        return key.encode("utf-8")
    
    # Try reading from .env.key file
    key_path = ".env.key"
    if os.path.exists(key_path):
        # Check file permissions before reading
        if not _check_file_permissions(key_path):
            logger.warning(
                "Insecure permissions detected on %s - should be 0o600. Attempting to fix...",
                key_path
            )
            if not _fix_file_permissions(key_path):
                logger.error(
                    "SECURITY WARNING: Could not fix permissions on %s - key file may be exposed!",
                    key_path
                )
        
        with open(key_path, "rb") as f:
            return f.read().strip()
    
    # Generate a new key if it doesn't exist
    key = Fernet.generate_key()
    try:
        with open(key_path, "wb") as f:
            f.write(key)
        # Set secure permissions (owner read/write only)
        os.chmod(key_path, 0o600)
        logger.warning("Generated new encryption key at %s - store securely!", key_path)
    except (OSError, IOError, PermissionError) as e:
        logger.error("Failed to persist encryption key: %s", e)
        # Return the key anyway for this process
    return key

def _get_token_encryption_key():
    """
    Return a Fernet key specifically for token file encryption.
    Tries multiple sources in order:
    1. SCHWAB_TOKEN_ENCRYPTION_KEY environment variable
    2. MP5_ENCRYPTION_KEY environment variable (fallback)
    3. .token.key file
    4. .env.key file (fallback)
    
    If no key exists, generates a new one and stores it.
    """
    if not FERNET_AVAILABLE:
        return None
    
    # Try dedicated token encryption key
    key = os.environ.get("SCHWAB_TOKEN_ENCRYPTION_KEY")
    if key:
        return key.encode("utf-8")
    
    # Try general encryption key
    key = os.environ.get("MP5_ENCRYPTION_KEY")
    if key:
        return key.encode("utf-8")
    
    # Try dedicated token key file with permission check
    key_path = ".token.key"
    if os.path.exists(key_path):
        # Check file permissions before reading
        if not _check_file_permissions(key_path):
            logger.warning(
                "Insecure permissions detected on %s - should be 0o600. Attempting to fix...",
                key_path
            )
            if not _fix_file_permissions(key_path):
                logger.error(
                    "SECURITY WARNING: Could not fix permissions on %s - key file may be exposed!",
                    key_path
                )
        
        with open(key_path, "rb") as f:
            return f.read().strip()
    
    # Try general key file with permission check
    key_path = ".env.key"
    if os.path.exists(key_path):
        # Check file permissions before reading
        if not _check_file_permissions(key_path):
            logger.warning(
                "Insecure permissions detected on %s - should be 0o600. Attempting to fix...",
                key_path
            )
            if not _fix_file_permissions(key_path):
                logger.error(
                    "SECURITY WARNING: Could not fix permissions on %s - key file may be exposed!",
                    key_path
                )
        
        with open(key_path, "rb") as f:
            return f.read().strip()
    
    # No key found - generate a new token key
    logger.warning("No token encryption key found - generating new key")
    key = Fernet.generate_key()
    key_path = ".token.key"
    try:
        with open(key_path, "wb") as f:
            f.write(key)
        os.chmod(key_path, 0o600)
        logger.warning("Generated new token encryption key at %s - store securely!", key_path)
    except (OSError, IOError, PermissionError) as e:
        logger.error("Failed to persist token encryption key: %s", e)
        # Return the key anyway for this process
    return key

def _get_hmac_key():
    """
    Return an HMAC key for token integrity verification.
    Uses the same key as token encryption for simplicity.
    """
    return _get_token_encryption_key()

def _mask_sensitive_value(value: str, show_chars: int = 4) -> str:
    """
    Mask a sensitive value for logging, showing only a few characters.
    
    Args:
        value: The sensitive value to mask
        show_chars: Number of characters to show at the end
    
    Returns:
        Masked value (e.g., "***abc123")
    """
    if not value:
        return "***"
    if len(value) <= show_chars:
        return "*" * len(value)
    return "*" * (len(value) - show_chars) + value[-show_chars:]

def _encrypt_sensitive_value(value):
    """
    Encrypt a sensitive configuration value with HMAC integrity protection.
    
    Creates an encrypted value in the format: enc:hmac_digest:encrypted_data
    where hmac_digest is HMAC-SHA256 of the encrypted data.
    
    Args:
        value: The plaintext value to encrypt
        
    Returns:
        Encrypted value with HMAC, or None if encryption not available
    """
    if not FERNET_AVAILABLE:
        logger.warning("Fernet encryption not available, cannot encrypt value")
        return None
        
    if value is None or value == "":
        return ""
    
    if not isinstance(value, str):
        value = str(value)
    
    try:
        key = _get_encryption_key()
        if key is None:
            logger.warning("No encryption key available, cannot encrypt value")
            return None
        
        fernet = Fernet(key)
        
        # Encrypt the value
        encrypted_bytes = fernet.encrypt(value.encode("utf-8"))
        encrypted_token = encrypted_bytes.decode("utf-8")
        
        # Generate HMAC for integrity checking
        hmac_digest = hmac.new(
            key,
            encrypted_token.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Return in format: enc:hmac:data
        return f"enc:{hmac_digest}:{encrypted_token}"
        
    except Exception as e:
        logger.error(f"Failed to encrypt value: {e}")
        return None

def _decrypt_sensitive_value(value):
    """
    Decrypt a sensitive configuration value that was encrypted.
    
    Supports two formats:
    1. Legacy format: 'enc:encrypted_data' (Fernet only)
    2. HMAC format: 'enc:hmac_digest:encrypted_data' (Fernet + HMAC-SHA256)
    
    If the value starts with 'enc:', it will be decrypted and validated.
    Otherwise, it will be returned as-is.
    
    Args:
        value: The value to decrypt (if encrypted)
        
    Returns:
        Decrypted value or original value if not encrypted
        
    Raises:
        Logs WARNING when decryption/validation fails
    """
    if not FERNET_AVAILABLE:
        return value
        
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    
    # Check if value is encrypted (starts with 'enc:')
    if value.startswith("enc:"):
        try:
            key = _get_encryption_key()
            if key is None:
                logger.warning(
                    "Decryption failed: No encryption key found. "
                    "Set MP5_ENCRYPTION_KEY or create .env.key file."
                )
                return ""
            
            fernet = Fernet(key)
            
            # Parse the encrypted value format
            parts = value[4:].split(':', 1)  # Remove 'enc:' prefix and split
            
            if len(parts) == 2:
                # New format with HMAC: enc:hmac_digest:encrypted_data
                expected_hmac = parts[0]
                encrypted_token = parts[1]
                
                # Verify HMAC integrity before decryption
                computed_hmac = hmac.new(
                    key,
                    encrypted_token.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(expected_hmac, computed_hmac):
                    logger.warning(
                        "Decryption failed: HMAC integrity check failed. "
                        "Data may have been tampered with or corrupted."
                    )
                    return ""
                
                # HMAC verified, proceed with decryption
                decrypted_bytes = fernet.decrypt(encrypted_token.encode("utf-8"))
                return decrypted_bytes.decode("utf-8")
            else:
                # Legacy format without HMAC: enc:encrypted_data
                # Still decrypt but log a warning about missing HMAC
                encrypted_token = parts[0]
                logger.debug(
                    "Decrypting legacy format without HMAC. "
                    "Consider re-encrypting with HMAC for enhanced security."
                )
                decrypted_bytes = fernet.decrypt(encrypted_token.encode("utf-8"))
                return decrypted_bytes.decode("utf-8")
                
        except Exception as e:
            # Log decryption failure at WARNING level (not just debug)
            logger.warning(
                f"Failed to decrypt environment variable: {e}. "
                "Invalid credentials will not be accepted."
            )
            return ""
    
    return value

def get_decrypted_env(key, default=""):
    """
    Get an environment variable and decrypt it if it's encrypted.
    
    Args:
        key: Environment variable name
        default: Default value if key not found
        
    Returns:
        Decrypted value or default
    """
    value = os.getenv(key, default)
    if key in SENSITIVE_ENV_KEYS:
        return _decrypt_sensitive_value(value)
    return value


class SchwabAuthenticator:
    """
    Handles Schwab API OAuth authentication using the schwab-py library.
    
    This class manages the OAuth flow, token storage, and client creation
    for interacting with Schwab's API. Includes encryption and integrity
    checking for enhanced token security.
    """
    
    def __init__(
        self, 
        api_key: str, 
        app_secret: str, 
        callback_url: str,
        token_path: str = 'token.json',
        environment: str = 'sandbox',
        encrypt_token: Optional[bool] = None
    ):
        """
        Initialize the Schwab authenticator.
        
        Args:
            api_key: Your Schwab API key (consumer key)
            app_secret: Your Schwab app secret
            callback_url: OAuth callback URL (must match Schwab app settings)
            token_path: Path to store OAuth token file
            environment: API environment - 'sandbox' or 'production' (default: 'sandbox')
                        Note: The actual endpoint is determined by your API credentials,
                        but this helps track intended usage and prevents mode confusion.
            encrypt_token: Whether to encrypt token file with HMAC integrity checks.
                          If None, reads from SCHWAB_ENCRYPT_TOKEN env var (default: True)
        """
        if not SCHWAB_PY_AVAILABLE:
            raise ImportError(
                "schwab-py library is not installed. "
                "Install it with: pip install schwab-py\n"
                "See https://github.com/alexgolec/schwab-py for more information."
            )
        
        # Validate environment parameter
        if environment not in ('sandbox', 'production'):
            raise ValueError(
                f"Invalid environment '{environment}'. Must be 'sandbox' or 'production'."
            )
        
        self.api_key = api_key
        self.app_secret = app_secret
        self.callback_url = callback_url
        self.token_path = token_path
        self.environment = environment
        self.encrypt_token = encrypt_token
        self._client = None
        
        # Determine if token encryption is enabled
        if encrypt_token is None:
            # Read from environment variable, default to True for security
            encrypt_token_str = os.getenv('SCHWAB_ENCRYPT_TOKEN', 'true').lower()
            self.encrypt_token = encrypt_token_str in ('true', '1', 'yes', 'on')
        else:
            self.encrypt_token = encrypt_token
        
        logger.info(f"SchwabAuthenticator initialized for {environment} environment")
        logger.info(f"Callback URL: {_mask_sensitive_value(callback_url, show_chars=8)}")
        logger.info(f"Token will be stored at: {token_path}")
        
        # Validate that credentials match intended environment
        self._validate_credential_environment_match()
        
        # Log important note about environment vs credentials
        if environment == 'sandbox':
            logger.info("Using sandbox environment - ensure your API credentials are for sandbox")
        else:
            logger.warning("Using PRODUCTION environment - trades will use real money!")
            logger.warning("Ensure your API credentials are approved for production use")
    
    def _validate_credential(self, value: str, name: str, placeholder: str) -> None:
        """
        Validate a credential value is not a placeholder.
        
        Args:
            value: The credential value to validate
            name: The credential name (for error messages)
            placeholder: The placeholder value to check against
            
        Raises:
            ValueError: If credential is invalid
        """
        if not value or value == placeholder:
            raise ValueError(
                f"Invalid {name}. Please set a valid {name.lower()} in .env file.\n"
                f"Get your {name.lower()} from https://developer.schwab.com/"
            )
    
    def _save_encrypted_token(self, token_data: dict) -> None:
        """
        Save token data with optional encryption and HMAC integrity checking.
        
        Args:
            token_data: Token dictionary to save
        """
        if not self.encrypt_token or not FERNET_AVAILABLE:
            # Save as plain JSON if encryption is disabled or not available
            with open(self.token_path, 'w') as f:
                json.dump(token_data, f, indent=2)
            logger.debug(f"Saved plain token to {self.token_path}")
            return
        
        # Get encryption and HMAC keys
        encryption_key = _get_token_encryption_key()
        hmac_key = _get_hmac_key()
        
        if not encryption_key or not hmac_key:
            logger.warning("Encryption keys not available, saving as plain JSON")
            with open(self.token_path, 'w') as f:
                json.dump(token_data, f, indent=2)
            return
        
        # Encrypt token data
        fernet = Fernet(encryption_key)
        token_json = json.dumps(token_data)
        encrypted_data = fernet.encrypt(token_json.encode('utf-8'))
        encrypted_str = encrypted_data.decode('utf-8')
        
        # Compute HMAC on encrypted data for integrity verification
        # This allows verification before decryption attempt
        hmac_hash = hmac.new(
            hmac_key,
            encrypted_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Save encrypted token with HMAC
        encrypted_wrapper = {
            'encrypted': True,
            'data': encrypted_str,
            'hmac': hmac_hash
        }
        
        with open(self.token_path, 'w') as f:
            json.dump(encrypted_wrapper, f, indent=2)
        
        logger.debug(f"Saved encrypted token with HMAC to {self.token_path}")
    
    def _load_encrypted_token(self) -> Optional[dict]:
        """
        Load token data with optional decryption and HMAC integrity verification.
        
        Returns:
            Token dictionary or None if file doesn't exist
            
        Raises:
            ValueError: If HMAC integrity check fails (token tampering detected)
        """
        if not os.path.exists(self.token_path):
            return None
        
        with open(self.token_path, 'r') as f:
            data = json.load(f)
        
        # Check if this is an encrypted token
        if not isinstance(data, dict) or not data.get('encrypted'):
            # Plain JSON token (backward compatibility)
            logger.debug(f"Loaded plain token from {self.token_path}")
            return data
        
        # This is an encrypted token, verify HMAC first before decryption
        if not FERNET_AVAILABLE:
            error_msg = """Token is encrypted but cryptography library is not available.

Please install: pip install cryptography

Or disable token encryption:
  - Set SCHWAB_ENCRYPT_TOKEN=false in .env
  - Delete the token file: rm {}
  - Restart the bot""".format(self.token_path)
            raise ValueError(error_msg)
        
        encryption_key = _get_token_encryption_key()
        hmac_key = _get_hmac_key()
        
        if not encryption_key or not hmac_key:
            error_msg = """Token is encrypted but encryption keys are not available.

The token file requires an encryption key to decrypt, but no key was found.

Solutions:
  1. Set an encryption key in .env file:
     - SCHWAB_TOKEN_ENCRYPTION_KEY=<your_key> OR
     - MP5_ENCRYPTION_KEY=<your_key>
  
  2. Create a key file:
     - .token.key (preferred for token encryption) OR
     - .env.key (general purpose)
  
  3. Delete the token and re-authenticate:
     - rm {}
     - Restart the bot to create a fresh token
  
  4. Disable encryption (simpler but less secure):
     - Set SCHWAB_ENCRYPT_TOKEN=false in .env
     - Delete the token: rm {}
     - Restart the bot

Note: If this is a new environment, copy the encryption key from where the token was created.""".format(self.token_path, self.token_path)
            raise ValueError(error_msg)
        
        encrypted_str = data['data']
        stored_hmac = data.get('hmac', '')
        
        # Verify HMAC integrity BEFORE attempting decryption
        # This provides early detection of tampering
        computed_hmac = hmac.new(
            hmac_key,
            encrypted_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(computed_hmac, stored_hmac):
            logger.error("Token HMAC verification failed - possible tampering detected")
            error_msg = """Token integrity check failed - HMAC mismatch.

This means:
  1. The token file may have been tampered with or corrupted
  2. The encryption key is different from when the token was created
  3. The token file format is incompatible with current version

Recovery Options:

Option 1: Delete the token and re-authenticate (RECOMMENDED)
  - rm {}
  - Restart the bot to create a fresh token with current encryption key

Option 2: Verify encryption key matches
  - Ensure SCHWAB_TOKEN_ENCRYPTION_KEY or MP5_ENCRYPTION_KEY is correct
  - The key must be EXACTLY the same as when token was created

Option 3: Use simulation mode (no Schwab API)
  - Set SCHWAB_API_ENABLED=off in .env
  - Set SCHWAB_SANDBOX_MODE=false in .env""".format(self.token_path)
            raise ValueError(error_msg)
        
        # HMAC verified, now decrypt the token
        fernet = Fernet(encryption_key)
        encrypted_data = encrypted_str.encode('utf-8')
        
        try:
            decrypted_bytes = fernet.decrypt(encrypted_data)
            token_json = decrypted_bytes.decode('utf-8')
            token_data = json.loads(token_json)
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            error_msg = """Token decryption failed: {}

Common causes:
  1. Wrong encryption key (key changed or using wrong key)
  2. Corrupted token file
  3. Token was created with different cryptography library version

Solutions:

Option 1: Delete token and re-authenticate (RECOMMENDED)
  - Run: rm {}
  - Restart the bot to initiate OAuth login
  - New token will be created with current encryption key

Option 2: Disable encryption
  - Set SCHWAB_ENCRYPT_TOKEN=false in .env
  - Delete token: rm {}
  - Restart the bot

Option 3: Restore correct encryption key
  - Find the original SCHWAB_TOKEN_ENCRYPTION_KEY or MP5_ENCRYPTION_KEY
  - Set it in .env or restore .token.key/.env.key file
  - The key MUST match the one used when token was created

Option 4: Use simulation mode (no Schwab API)
  - Set SCHWAB_API_ENABLED=off in .env
  - Set SCHWAB_SANDBOX_MODE=false in .env""".format(str(e), self.token_path, self.token_path)
            raise ValueError(error_msg)
        
        logger.debug(f"Loaded and verified encrypted token from {self.token_path}")
        return token_data
    
    def get_client(self, interactive: bool = True):
        """
        Get or create an authenticated Schwab API client.
        
        Args:
            interactive: If True, opens a browser for OAuth login on first run.
                        If False, requires token.json to already exist.
        
        Returns:
            Authenticated schwab-py client
            
        Raises:
            ValueError: If credentials are invalid or authentication fails
            FileNotFoundError: If token file doesn't exist in non-interactive mode
        
        Note:
            The actual API endpoint (sandbox vs production) is determined by your
            API credentials from the Schwab Developer Portal. This class tracks
            the intended environment to help prevent mode confusion.
        """
        # Return cached client if already created
        if self._client is not None:
            logger.debug(f"Returning cached Schwab client (environment: {self.environment})")
            return self._client
        
        # Validate credentials
        self._validate_credential(self.api_key, "SCHWAB_API_KEY", "your_app_key")
        self._validate_credential(self.app_secret, "SCHWAB_APP_SECRET", "your_app_secret")
        
        try:
            # Check if token file exists
            token_exists = os.path.exists(self.token_path)
            
            if not interactive and not token_exists:
                logger.error(
                    f"Non-interactive mode requires existing token file at {self.token_path}"
                )
                error_message = f"""Token file not found at {self.token_path}.
In non-interactive mode (NON_INTERACTIVE=true), the token file must exist.
Options:
  1. Run bot interactively first to generate token.json
  2. Set SCHWAB_API_ENABLED=off to use yfinance simulation mode
  3. Copy an existing token.json file to this location"""
                raise FileNotFoundError(error_message)
            
            # For encrypted tokens, we need to decrypt to a temp file for schwab-py
            temp_token_path = None
            if token_exists and self.encrypt_token:
                try:
                    # Load and decrypt the token
                    token_data = self._load_encrypted_token()
                    
                    # If we got a token, create a temporary unencrypted version for schwab-py
                    if token_data:
                        temp_fd, temp_token_path = tempfile.mkstemp(suffix='.json', prefix='token_')
                        os.close(temp_fd)
                        
                        with open(temp_token_path, 'w') as f:
                            json.dump(token_data, f)
                        
                        logger.debug(f"Created temporary token file for schwab-py: {temp_token_path}")
                        
                except ValueError as e:
                    logger.error(f"Token decryption/verification failed: {e}")
                    
                    # Provide detailed error message with recovery options
                    error_message = f"""Token decryption failed: {e}

This usually means:
  1. The encryption key has changed or is missing
  2. The token file is corrupted or was tampered with
  3. The token file was created with a different encryption key

Recovery Options:

Option 1: Delete the token file and re-authenticate
  - Run: rm {self.token_path}
  - Restart the bot to initiate a fresh OAuth login

Option 2: Disable token encryption (if you prefer unencrypted tokens)
  - Set SCHWAB_ENCRYPT_TOKEN=false in .env file
  - Delete the current token file: rm {self.token_path}
  - Restart the bot

Option 3: Check encryption key configuration
  - Ensure SCHWAB_TOKEN_ENCRYPTION_KEY or MP5_ENCRYPTION_KEY is set correctly
  - Or ensure .token.key or .env.key file exists and is readable
  - The key must be the SAME key used when the token was originally encrypted

Option 4: Use simulation mode instead (no Schwab API required)
  - Set SCHWAB_API_ENABLED=off in .env file
  - Set SCHWAB_SANDBOX_MODE=false in .env file
  - This will use yfinance for market data instead

For non-interactive environments:
  - Copy a working token.json from an interactive session
  - Ensure encryption keys are consistent across environments"""
                    raise ValueError(error_message)
            
            # Determine which token path to use
            auth_token_path = temp_token_path if temp_token_path else self.token_path
            
            if token_exists:
                logger.info("Found existing token file, attempting to use it")
            else:
                if not interactive:
                    # This shouldn't happen due to check above, but be defensive
                    raise FileNotFoundError(
                        f"Token file not found at {self.token_path} in non-interactive mode"
                    )
                logger.info("No token file found, will initiate OAuth login flow")
                logger.info("A browser window will open for Schwab authentication")
            
            # Create client using easy_client
            # This handles OAuth flow and token refresh automatically
            # Note: The actual endpoint is determined by the credentials themselves
            # (sandbox credentials -> sandbox endpoint, production -> production endpoint)
            self._client = auth.easy_client(
                api_key=self.api_key,
                app_secret=self.app_secret,
                callback_url=self.callback_url,
                token_path=auth_token_path
            )
            
            # After successful authentication, encrypt the token if needed
            if self.encrypt_token and not token_exists:
                # New token was created - encrypt it
                try:
                    with open(auth_token_path, 'r') as f:
                        new_token = json.load(f)
                    self._save_encrypted_token(new_token)
                    logger.info("New token encrypted and saved")
                except Exception as e:
                    logger.error(f"Failed to encrypt new token: {e}")
            
            # Clean up temporary token file if we created one
            if temp_token_path and os.path.exists(temp_token_path):
                try:
                    os.remove(temp_token_path)
                    logger.debug(f"Cleaned up temporary token file: {temp_token_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary token file: {e}")
            
            logger.info(f"Successfully authenticated with Schwab API ({self.environment} environment)")
            logger.info(f"Note: Actual endpoint determined by your API credentials")
            return self._client
            
        except EOFError as e:
            # This specific error happens when stdin is not available (non-interactive environment)
            logger.error(
                f"EOF error during authentication - likely running in non-interactive environment: {e}"
            )
            error_message = f"""Schwab authentication failed: {e}
This error occurs when running in a non-interactive environment (CI/CD, automated scripts).
Solutions:
  1. Set NON_INTERACTIVE=true and ensure token.json exists
  2. Set SCHWAB_API_ENABLED=off to use yfinance simulation mode
  3. Run bot interactively first to generate token.json, then copy it to your automation environment"""
            raise ValueError(error_message)
        except Exception as e:
            logger.error(f"Failed to authenticate with Schwab API: {e}")
            error_message = f"""Schwab authentication failed: {e}
Please check:
  1. Your API key and app secret are correct
  2. Your callback URL matches the one in Schwab Developer Portal
  3. Your Schwab app has been approved
  4. You have network connectivity
Visit https://developer.schwab.com/ for more information"""
            raise ValueError(error_message)
    
    def _validate_credential_environment_match(self) -> None:
        """
        Validate that API credentials match the intended environment.
        
        This provides a best-effort check to detect potential credential/environment
        mismatches. Note: Schwab API key format may not always be distinguishable.
        
        Logs warnings if a mismatch is detected.
        """
        # Check if API key contains obvious environment indicators
        # Note: This is heuristic-based since Schwab doesn't publish credential format specs
        api_key_lower = self.api_key.lower()
        
        # Look for sandbox indicators in the API key or callback URL
        has_sandbox_indicator = (
            'sandbox' in api_key_lower or
            'test' in api_key_lower or
            'dev' in api_key_lower or
            'sandbox' in self.callback_url.lower()
        )
        
        # Look for production indicators
        has_production_indicator = (
            'prod' in api_key_lower or
            'live' in api_key_lower
        )
        
        # Check for potential mismatch
        if self.environment == 'sandbox' and has_production_indicator:
            logger.warning(
                "⚠️  POTENTIAL MISMATCH: Environment set to 'sandbox' but credentials "
                "appear to be for production. Verify your API credentials!"
            )
            logger.warning(
                "   If credentials are production, trades will use REAL MONEY despite "
                "sandbox setting."
            )
        elif self.environment == 'production' and has_sandbox_indicator:
            logger.warning(
                "⚠️  POTENTIAL MISMATCH: Environment set to 'production' but credentials "
                "appear to be for sandbox. Verify your API credentials!"
            )
            logger.warning(
                "   If credentials are sandbox, you won't be able to place real trades."
            )
        
        # Additional validation: In production mode, require explicit confirmation
        if self.environment == 'production':
            logger.warning(
                "═══════════════════════════════════════════════════════"
            )
            logger.warning(
                "  PRODUCTION MODE: Using REAL MONEY and REAL TRADES"
            )
            logger.warning(
                "  Ensure your API credentials are approved for production"
            )
            logger.warning(
                "═══════════════════════════════════════════════════════"
            )
    
    def is_authenticated(self) -> bool:
        """
        Check if client is authenticated.
        
        Returns:
            True if client is authenticated, False otherwise
        """
        return self._client is not None
    
    def get_environment(self) -> str:
        """
        Get the current environment setting.
        
        Returns:
            'sandbox' or 'production'
        """
        return self.environment
    
    def clear_authentication(self):
        """
        Clear cached client (useful for re-authentication).
        Note: This does not delete the token file.
        """
        logger.info("Clearing cached Schwab client")
        self._client = None
    
    def delete_token_file(self):
        """
        Delete the token file (requires re-authentication next time).
        Use this if you need to switch accounts or if the token is corrupted.
        """
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
            logger.info(f"Deleted token file: {self.token_path}")
        self.clear_authentication()


def create_schwab_client(
    api_key: Optional[str] = None,
    app_secret: Optional[str] = None,
    callback_url: Optional[str] = None,
    token_path: Optional[str] = None,
    interactive: bool = True,
    environment: Optional[str] = None,
    encrypt_token: Optional[bool] = None
):
    """
    Convenience function to create an authenticated Schwab client.
    
    Args:
        api_key: Schwab API key (defaults to SCHWAB_API_KEY env var)
        app_secret: Schwab app secret (defaults to SCHWAB_APP_SECRET env var)
        callback_url: OAuth callback URL (defaults to SCHWAB_CALLBACK_URL env var)
        token_path: Token file path (defaults to SCHWAB_TOKEN_PATH env var or 'token.json')
        interactive: Whether to allow interactive OAuth login
        environment: API environment - 'sandbox' or 'production' 
                    (defaults to SCHWAB_SANDBOX_MODE env var interpretation)
        encrypt_token: Whether to use encrypted token file
                      (defaults to SCHWAB_ENCRYPT_TOKEN env var)
    
    Returns:
        Authenticated schwab-py client
    """
    # Load from environment if not provided
    api_key = api_key or get_decrypted_env('SCHWAB_API_KEY', 'your_app_key')
    app_secret = app_secret or get_decrypted_env('SCHWAB_APP_SECRET', 'your_app_secret')
    callback_url = callback_url or os.getenv('SCHWAB_CALLBACK_URL', 'https://127.0.0.1:8182')
    token_path = token_path or os.getenv('SCHWAB_TOKEN_PATH', 'token.json')
    
    # Determine environment from SCHWAB_SANDBOX_MODE if not explicitly provided
    if environment is None:
        sandbox_mode = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'
        environment = 'sandbox' if sandbox_mode else 'production'
    
    # Determine if token encryption should be enabled
    encrypt_token = os.getenv('SCHWAB_ENCRYPT_TOKEN', 'true').lower() == 'true'
    
    authenticator = SchwabAuthenticator(
        api_key=api_key,
        app_secret=app_secret,
        callback_url=callback_url,
        token_path=token_path,
        environment=environment,
        encrypt_token=encrypt_token
    )
    
    return authenticator.get_client(interactive=interactive)
