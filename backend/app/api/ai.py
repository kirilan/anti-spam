from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import AiSettingsStatus, AiSettingsUpdate
from app.services.ai_settings import DEFAULT_GEMINI_MODEL, choose_model, resolve_model
from app.services.gemini_service import GeminiServiceError, list_gemini_models

router = APIRouter()


@router.get("/key/status", response_model=AiSettingsStatus)
def gemini_key_status(current_user: User = Depends(get_current_user)):
    available_models = []
    if current_user.encrypted_gemini_api_key:
        api_key = current_user.get_gemini_api_key()
        try:
            available_models = list_gemini_models(api_key)
        except GeminiServiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    model = resolve_model(current_user.gemini_model)
    if available_models:
        model = choose_model(available_models, None, current_user.gemini_model)

    return AiSettingsStatus(
        has_key=bool(current_user.encrypted_gemini_api_key),
        updated_at=current_user.gemini_key_updated_at,
        model=model,
        available_models=available_models,
    )


@router.put("/key", response_model=AiSettingsStatus)
def update_gemini_key(
    payload: AiSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.api_key is None and payload.model is None:
        raise HTTPException(status_code=400, detail="No settings provided")

    available_models = []

    if payload.api_key is not None:
        if not payload.api_key.strip():
            raise HTTPException(status_code=400, detail="API key cannot be empty")
        api_key = payload.api_key.strip()
        try:
            available_models = list_gemini_models(api_key)
        except GeminiServiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        if not available_models:
            raise HTTPException(status_code=400, detail="No models available for this API key")
        current_user.set_gemini_api_key(api_key)

    if not available_models and current_user.encrypted_gemini_api_key:
        api_key = current_user.get_gemini_api_key()
        try:
            available_models = list_gemini_models(api_key)
        except GeminiServiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    if payload.model is not None:
        candidate = payload.model.strip()
        if not available_models:
            raise HTTPException(status_code=400, detail="No models available to validate selection")
        if candidate not in available_models:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported model. Supported: {', '.join(sorted(available_models))}",
            )
        current_user.gemini_model = candidate
    elif available_models:
        current_user.gemini_model = choose_model(
            available_models,
            None,
            current_user.gemini_model,
        )
    db.commit()
    db.refresh(current_user)

    return AiSettingsStatus(
        has_key=bool(current_user.encrypted_gemini_api_key),
        updated_at=current_user.gemini_key_updated_at,
        model=resolve_model(current_user.gemini_model),
        available_models=available_models,
    )


@router.delete("/key", response_model=AiSettingsStatus)
def delete_gemini_key(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.encrypted_gemini_api_key:
        return AiSettingsStatus(
            has_key=False,
            updated_at=current_user.gemini_key_updated_at,
            model=resolve_model(current_user.gemini_model),
            available_models=[],
        )

    current_user.clear_gemini_api_key()
    if not current_user.gemini_model:
        current_user.gemini_model = DEFAULT_GEMINI_MODEL
    db.commit()
    db.refresh(current_user)

    return AiSettingsStatus(
        has_key=bool(current_user.encrypted_gemini_api_key),
        updated_at=current_user.gemini_key_updated_at,
        model=resolve_model(current_user.gemini_model),
        available_models=[],
    )
