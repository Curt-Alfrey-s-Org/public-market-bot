# Sandbox/Live Environment Distinction in Authentication

## Overview

This document describes the sandbox/live environment distinction implementation in `schwab_auth.py` to prevent mode confusion and improve clarity when working with Schwab's API.

## Problem Statement

Previously, `schwab_auth.py` lacked explicit sandbox/live switching. The `easy_client` function had no `base_url` parameter, which could cause mode confusion despite guards elsewhere in the codebase. Users might not know if they were connecting to sandbox or production endpoints.

## Solution

We added an explicit `environment` parameter to track the intended API environment (sandbox or production). While the actual endpoint is determined by the API credentials themselves (as per schwab-py library design), this tracking helps prevent mode confusion through:

1. **Clear initialization logging** - Shows which environment is intended
2. **Environment validation** - Rejects invalid environment values
3. **Mode awareness** - Provides a getter method to check current environment
4. **Integration with SCHWAB_SANDBOX_MODE** - Automatically determines environment from configuration

## Implementation Details

### Changes to `SchwabAuthenticator` Class

#### New `__init__` Parameter

```python
def __init__(
    self, 
    api_key: str, 
    app_secret: str, 
    callback_url: str,
    token_path: str = 'token.json',
    environment: str = 'sandbox'  # NEW PARAMETER
):
```

- **Parameter**: `environment` (str)
- **Valid values**: `'sandbox'` or `'production'`
- **Default**: `'sandbox'`
- **Validation**: Raises `ValueError` if invalid value provided

#### Enhanced Logging

The authenticator now logs:
- Which environment is initialized (sandbox or production)
- Reminder that credentials determine actual endpoint
- Production mode warning about real money usage

Example log output for sandbox:
```
INFO: SchwabAuthenticator initialized for sandbox environment
INFO: Callback URL: https://127.0.0.1:8182
INFO: Token will be stored at: token.json
INFO: Using sandbox environment - ensure your API credentials are for sandbox
```

Example log output for production:
```
INFO: SchwabAuthenticator initialized for production environment
INFO: Callback URL: https://127.0.0.1:8182
INFO: Token will be stored at: token.json
WARNING: Using PRODUCTION environment - trades will use real money!
WARNING: Ensure your API credentials are approved for production use
```

#### New Method: `get_environment()`

```python
def get_environment(self) -> str:
    """
    Get the current environment setting.
    
    Returns:
        'sandbox' or 'production'
    """
    return self.environment
```

### Changes to `create_schwab_client` Function

#### New Parameter

```python
def create_schwab_client(
    api_key: Optional[str] = None,
    app_secret: Optional[str] = None,
    callback_url: Optional[str] = None,
    token_path: Optional[str] = None,
    interactive: bool = True,
    environment: Optional[str] = None  # NEW PARAMETER
):
```

- **Parameter**: `environment` (Optional[str])
- **Default behavior**: If `None`, automatically determined from `SCHWAB_SANDBOX_MODE` environment variable
  - `SCHWAB_SANDBOX_MODE=true` → `environment='sandbox'`
  - `SCHWAB_SANDBOX_MODE=false` → `environment='production'`
- **Explicit override**: Can be set explicitly to override `SCHWAB_SANDBOX_MODE`

### Changes to `main.py`

Updated `_initialize_schwab_authenticator` method to pass environment parameter:

```python
# Determine environment based on SCHWAB_SANDBOX_MODE
environment = 'sandbox' if SCHWAB_SANDBOX_MODE else 'production'

self.schwab_authenticator = SchwabAuthenticator(
    api_key=SCHWAB_API_KEY,
    app_secret=SCHWAB_APP_SECRET,
    callback_url=SCHWAB_CALLBACK_URL,
    token_path=SCHWAB_TOKEN_PATH,
    environment=environment  # NEW PARAMETER
)
```

## Usage Examples

### Example 1: Sandbox Mode (Default)

```python
from schwab_auth import SchwabAuthenticator

# Explicitly specify sandbox
auth = SchwabAuthenticator(
    api_key="change-me",
    app_secret="change-me",
    callback_url="https://127.0.0.1:8182",
    token_path="token.json",
    environment="sandbox"
)

client = auth.get_client(interactive=True)
print(f"Connected to: {auth.get_environment()}")  # Output: sandbox
```

### Example 2: Production Mode

```python
from schwab_auth import SchwabAuthenticator

# Explicitly specify production
auth = SchwabAuthenticator(
    api_key="change-me",
    app_secret="change-me",
    callback_url="https://127.0.0.1:8182",
    token_path="token.json",
    environment="production"
)

client = auth.get_client(interactive=True)
print(f"Connected to: {auth.get_environment()}")  # Output: production
```

### Example 3: Using Convenience Function with Environment Variable

```python
import os
from schwab_auth import create_schwab_client

# Set environment variable
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'

# Automatically uses sandbox based on environment variable
client = create_schwab_client(
    api_key="change-me",
    app_secret="change-me",
    interactive=True
)
```

### Example 4: Explicit Override of Environment Variable

```python
import os
from schwab_auth import create_schwab_client

# Environment variable says sandbox
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'

# But explicitly override to production
client = create_schwab_client(
    api_key="change-me",
    app_secret="change-me",
    interactive=True,
    environment="production"  # Explicit override
)
```

## Important Notes

### How Schwab API Endpoints Work

The **actual API endpoint** (sandbox vs production) is determined by your **API credentials**, not by any parameter in the code:

1. **Sandbox credentials** → Connect to `https://api.schwabapi.com` (sandbox)
2. **Production credentials** → Connect to `https://api.schwab.com` (production)

You obtain these credentials from the Schwab Developer Portal:
- New apps start in sandbox by default
- Apps must be "promoted" to production through the portal
- Production credentials are issued after promotion

### Purpose of Environment Parameter

The `environment` parameter in this implementation serves to:
- **Track intent**: Document which environment you intend to use
- **Improve logging**: Provide clear feedback about the environment
- **Prevent confusion**: Raise awareness of sandbox vs production mode
- **Enable validation**: Allow future checks to ensure credentials match intended environment

### Credential Mismatch Scenarios

**Scenario 1**: Sandbox credentials with `environment="production"`
- The code sets `environment="production"`
- But your credentials are sandbox credentials
- **Result**: Connects to sandbox (credentials win)
- **Recommendation**: Ensure your `environment` parameter matches your credentials

**Scenario 2**: Production credentials with `environment="sandbox"`
- The code sets `environment="sandbox"`
- But your credentials are production credentials
- **Result**: Connects to production (credentials win)
- **⚠️ DANGER**: You think you're in sandbox but trades are real!
- **Recommendation**: Always verify credentials match intended environment

## Testing

Run the test suite to verify sandbox/live distinction:

```bash
python3 test_sandbox_live_distinction.py
```

Test coverage includes:
- Environment parameter validation
- Default environment behavior
- Environment getter method
- Integration with `SCHWAB_SANDBOX_MODE`
- Explicit environment override

## Migration Guide

### For Existing Code

If you have existing code that creates `SchwabAuthenticator`:

**Before:**
```python
auth = SchwabAuthenticator(
    api_key=api_key,
    app_secret=app_secret,
    callback_url=callback_url,
    token_path=token_path
)
```

**After (backward compatible):**
```python
auth = SchwabAuthenticator(
    api_key=api_key,
    app_secret=app_secret,
    callback_url=callback_url,
    token_path=token_path,
    environment="sandbox"  # Optional, defaults to 'sandbox'
)
```

The change is **backward compatible** - if you don't specify `environment`, it defaults to `'sandbox'`.

### Configuration in .env

No changes needed to `.env` file. The existing `SCHWAB_SANDBOX_MODE` variable continues to work:

```bash
# For sandbox testing
SCHWAB_SANDBOX_MODE=true

# For production (real money)
SCHWAB_SANDBOX_MODE=false
```

## Security Considerations

1. **Always verify your credentials match your intended environment**
2. **Production credentials should never be committed to version control**
3. **Use `.env` files (not committed) for credential storage**
4. **Production mode warnings are logged to help prevent accidental real trades**
5. **Review logs before running in production mode**

## Future Enhancements

Potential future improvements:
1. **Credential validation**: Check if credentials match intended environment
2. **Environment detection**: Attempt to detect environment from credential format
3. **Confirmation prompt**: Require explicit confirmation for production mode
4. **Credential rotation**: Support for refreshing production credentials

## References

- Schwab Developer Portal: https://developer.schwab.com/
- schwab-py Documentation: https://schwab-py.readthedocs.io/
- schwab-py GitHub: https://github.com/alexgolec/schwab-py
- Issue: "Missing Sandbox/Live Distinction in Auth"
