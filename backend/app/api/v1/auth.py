from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    current_active_user,
)
from app.database import get_async_session
from app.models.user import User, UserRole, RoleType

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    school_id: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
) -> Token:
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # Get user's primary role
    role_result = await session.execute(
        select(UserRole).where(UserRole.user_id == user.id).limit(1)
    )
    user_role = role_result.scalar_one_or_none()
    role_name = user_role.role if user_role else "student"

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "school_id": str(user.school_id), "role": role_name},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer", role=role_name)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(current_active_user),
) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        school_id=str(current_user.school_id),
        is_active=current_user.is_active,
    )
