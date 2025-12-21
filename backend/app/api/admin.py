from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import TokenRevokeResponse, UserRoleUpdate, UserSummary

router = APIRouter()


@router.get("/users", response_model=list[UserSummary])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all users."""
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
    current_user: User = Depends(get_current_user),
):
    """Promote or demote a user."""

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
    current_user: User = Depends(get_current_user),
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
