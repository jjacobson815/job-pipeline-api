"""
API routes for user registration, authentication tokens, and user profile management.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.models import User
from app.domains.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


# --- Schemas -------------------------------------------------------------

class UserRegister(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserProfile(BaseModel):
    id: int
    email: str
    resume_text: str | None
    gemini_api_key: str | None
    teal_api_key: str | None


class ProfileUpdate(BaseModel):
    resume_text: str | None = None
    gemini_api_key: str | None = None
    teal_api_key: str | None = None


# --- Dependencies --------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency wrapper to resolve current logged-in User or abort with 401."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email: str | None = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# --- Endpoints -----------------------------------------------------------

@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, db: Session = Depends(get_db)) -> Any:
    """Create a new user account."""
    existing_user = db.query(User).filter(User.email == body.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered."
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        resume_text="",
        gemini_api_key=None,
        teal_api_key=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Successfully registered user account: %s", user.email)
    return user


@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """Login and acquire bearer access token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)) -> Any:
    """Retrieve current logged-in user profile details."""
    return current_user


@router.put("/me", response_model=UserProfile)
def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update current user profile fields."""
    if body.resume_text is not None:
        current_user.resume_text = body.resume_text
    if body.gemini_api_key is not None:
        # Strip whitespaces or handle clear-outs
        val = body.gemini_api_key.strip()
        current_user.gemini_api_key = val if val else None
    if body.teal_api_key is not None:
        val = body.teal_api_key.strip()
        current_user.teal_api_key = val if val else None

    db.commit()
    db.refresh(current_user)
    logger.info("Updated user profile settings for: %s", current_user.email)
    return current_user
