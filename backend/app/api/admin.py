from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.user import UserSummary, UserRoleUpdate, TokenRevokeResponse

router = APIRouter()


@router.get("/users", response_model=List[UserSummary])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return all users for admin management."""
    users = db.query(User).order_by(User.created_at.asc()).all()
    return [
        UserSummary(
            id=str(user.id),
            email=user.email,
            google_id=user.google_id,
            is_admin=user.is_admin,
            last_scan_at=user.last_scan_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        for user in users
    ]


@router.patch("/users/{user_id}/role", response_model=UserSummary)
def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Promote or demote a user."""
    if str(current_admin.id) == user_id and not payload.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own admin access.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = payload.is_admin
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserSummary(
        id=str(user.id),
        email=user.email,
        google_id=user.google_id,
        is_admin=user.is_admin,
        last_scan_at=user.last_scan_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/users/{user_id}/revoke-tokens", response_model=TokenRevokeResponse)
def revoke_user_tokens(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Strip stored Gmail tokens so the user must re-authenticate."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.encrypted_access_token = None
    user.encrypted_refresh_token = None
    db.add(user)
    db.commit()

    return TokenRevokeResponse(
        message="User tokens revoked. They must reconnect Gmail on next login.",
    )
