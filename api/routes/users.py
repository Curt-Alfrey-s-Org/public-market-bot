"""
User management endpoints (admin only).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from api.auth import get_current_user, hash_password
from api.models.user import User
from api.models.audit import AuditLog
from api.models.auth_token import EmailVerificationToken, PasswordResetToken
from api.models.backup_code import BackupCode
from database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UpdateUserRequest(BaseModel):
    role: str


class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: require admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_authenticated(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: require any authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user


@router.get("", response_model=UserListResponse)
async def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """List all users (admin only)."""
    users = db.query(User).all()
    return UserListResponse(
        total=len(users),
        users=[UserResponse.from_orm(u) for u in users]
    )


@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get user details (admin only)."""
    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)


@router.put("/{username}")
async def update_user(
    username: str,
    body: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update user role (admin only)."""
    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate role
    if body.role not in ("user", "admin", "moderator"):
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user.role = body.role
    db.add(AuditLog(
        user_id=current_user.get("sub") if isinstance(current_user.get("sub"), int) else None,
        event_type="user_role_updated",
        success=True,
        details=f"User {username} role changed to {body.role}"
    ))
    db.commit()
    
    return {"message": f"User {username} updated"}


@router.delete("/{username}")
async def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete user (admin only)."""
    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Rows that reference users.id (FK, no ON DELETE) must go first, or Postgres
    # rejects the delete with an IntegrityError (500) for every user who ever
    # registered or logged in. Audit rows are kept, just detached from the user.
    db.query(EmailVerificationToken).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(PasswordResetToken).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(BackupCode).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(AuditLog).filter_by(user_id=user.id).update({AuditLog.user_id: None}, synchronize_session=False)
    db.add(AuditLog(
        user_id=current_user.get("sub") if isinstance(current_user.get("sub"), int) else None,
        event_type="user_deleted",
        success=True,
        details=f"User {username} deleted"
    ))
    db.delete(user)
    db.commit()
    
    return {"message": f"User {username} deleted"}


@router.get("/profile/me", response_model=UserResponse)
async def get_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated)
):
    """Get current user profile (any authenticated user)."""
    username = current_user.get("sub", current_user.get("role"))
    user = db.query(User).filter_by(username=username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    return UserResponse.from_orm(user)
