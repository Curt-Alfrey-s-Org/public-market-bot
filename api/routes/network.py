"""
Network/Internet Access Control Routes
Allows users to allow/forbid bot internet connectivity
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.auth import require_admin  # changing internet access: admin JWT only
import os
import sys
from pathlib import Path

# internet_access_control.py lives at the project root (copied to /app in the
# container). Inserting api/ here (the old behavior) made api/main.py shadow the
# root main.py for any later `from main import TradingBot`.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
from internet_access_control import InternetAccessControl

router = APIRouter()
# config_dir stays api/ — the access-control JSON has always lived there.
internet_control = InternetAccessControl(config_dir=str(Path(__file__).parent.parent))

class InternetAccessRequest(BaseModel):
    allowed: bool

class InternetAccessResponse(BaseModel):
    allowed: bool
    allowed_str: str
    updated_at: str = None
    message: str = None

@router.get("/network/access", response_model=InternetAccessResponse)
async def get_internet_access():
    """Get current internet access status
    
    Returns:
        Current internet access setting (ALLOWED or FORBIDDEN)
    """
    try:
        config = internet_control.get_internet_access()
        return InternetAccessResponse(
            allowed=config.get('allowed', True),
            allowed_str=config.get('allowed_str', 'UNKNOWN'),
            updated_at=config.get('updated_at'),
            message="Internet access is " + config.get('allowed_str', 'UNKNOWN')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get internet access: {str(e)}")

@router.post("/network/access", response_model=InternetAccessResponse, dependencies=[Depends(require_admin)])
async def set_internet_access(request: InternetAccessRequest):
    """Set internet access status
    
    Args:
        request: {allowed: true|false}
        
    Returns:
        Updated internet access setting
    """
    try:
        config = internet_control.set_internet_access(request.allowed)
        action = "ALLOWED" if request.allowed else "FORBIDDEN"
        return InternetAccessResponse(
            allowed=config.get('allowed', True),
            allowed_str=config.get('allowed_str', 'UNKNOWN'),
            updated_at=config.get('updated_at'),
            message=f"Internet access is now {action}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set internet access: {str(e)}")

# State-changing GET (toggles the outbound firewall): admin JWT only, like POST /network/access.
@router.get("/network/access/forbid", response_model=InternetAccessResponse, dependencies=[Depends(require_admin)])
async def forbid_internet():
    """Forbid internet access (convenience endpoint)
    
    Returns:
        Updated status with internet access FORBIDDEN
    """
    config = internet_control.set_internet_access(False)
    return InternetAccessResponse(
        allowed=False,
        allowed_str="FORBIDDEN",
        updated_at=config.get('updated_at'),
        message="Internet access is now FORBIDDEN"
    )

# State-changing GET (toggles the outbound firewall): admin JWT only, like POST /network/access.
@router.get("/network/access/allow", response_model=InternetAccessResponse, dependencies=[Depends(require_admin)])
async def allow_internet():
    """Allow internet access (convenience endpoint)
    
    Returns:
        Updated status with internet access ALLOWED
    """
    config = internet_control.set_internet_access(True)
    return InternetAccessResponse(
        allowed=True,
        allowed_str="ALLOWED",
        updated_at=config.get('updated_at'),
        message="Internet access is now ALLOWED"
    )
