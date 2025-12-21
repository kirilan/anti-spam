from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies.auth import (
    create_access_token,
    get_current_user,
)
from app.models.user import User
from app.schemas.auth import AuthStatus
from app.services.gmail_service import GmailService

router = APIRouter()
gmail_service = GmailService()


@router.get("/login")
def login():
    """Initiate OAuth login flow"""
    authorization_url, state = gmail_service.get_authorization_url()

    return {"authorization_url": authorization_url, "state": state}


@router.get("/callback")
def oauth_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    """Handle OAuth callback from Google"""
    try:
        # Exchange code for tokens
        token_data = gmail_service.exchange_code_for_tokens(code, state)

        # Create temporary credentials to get user info
        from google.oauth2.credentials import Credentials

        temp_credentials = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_uri=token_data["token_uri"],
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"],
            scopes=token_data["scopes"],
        )

        # Get user info
        user_info = gmail_service.get_user_info(temp_credentials)

        # Check if user exists
        user = db.query(User).filter(User.google_id == user_info["id"]).first()

        if not user:
            # Create new user
            user = User(email=user_info["email"], google_id=user_info["id"])
            db.add(user)

        # Update tokens
        user.set_access_token(token_data["access_token"])
        user.set_refresh_token(token_data["refresh_token"])

        db.commit()
        db.refresh(user)

        # Issue JWT token
        token = create_access_token(
            subject=str(user.id),
            email=user.email,
            is_admin=user.is_admin,
            expires_delta_seconds=60 * 60 * 12,
        )

        params = urlencode(
            {
                "user_id": str(user.id),
                "email": user.email,
                "token": token,
            }
        )

        callback_url = f"{settings.frontend_url}/oauth-callback?{params}"
        return RedirectResponse(url=callback_url)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.get("/status", response_model=AuthStatus)
def auth_status(current_user: User = Depends(get_current_user)):
    """Validate authentication token and return user info"""
    from app.schemas.auth import User as UserSchema

    return AuthStatus(
        is_authenticated=True,
        user=UserSchema(
            id=str(current_user.id),
            email=current_user.email,
            google_id=current_user.google_id,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            is_admin=current_user.is_admin,
        ),
        message="User is authenticated",
        token=None,
    )
