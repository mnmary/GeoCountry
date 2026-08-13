
"""роутер нашего сервиса пользователи"""
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import create_access_token, create_refresh_token, decode_token
from app.dependencies import get_user_service
from app.schemas import UserCreate, UserRead, TokenResponse, RefreshTokenRequest
from app.user_service import UserService

users_router = APIRouter(prefix = "/users", tags = ["Пользователи"])

@users_router.post("/", response_model=UserRead, status_code=201)
async def create_user(
        user: UserCreate,
        user_service: UserService = Depends(get_user_service)
):
    """создаем пользователя с правами user"""
    # проверим, что юзера не существует
    ex_user = await user_service.get_user_by_email(str(user.email))
    if ex_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    new_user = await user_service.create_user(user)
    return new_user

@users_router.post("/login", response_model=TokenResponse)
async def login_user(
        user: OAuth2PasswordRequestForm = Depends(),
        user_service: UserService = Depends(get_user_service)
):
    """заходим в систему"""
    ex_user = await user_service.get_user_by_email(user.username)  # !! password form!!
    if not ex_user:
        raise HTTPException(status_code=401, detail="неверный email или пароль")
    is_valid = user_service.verify_password(user.password, ex_user.hashed_password)
    if not is_valid:
        raise HTTPException(status_code=401, detail="пароль неверный")

    # создаем токены
    access_token = create_access_token(ex_user.id)
    refresh_token = create_refresh_token(ex_user.id)

    await user_service.save_refresh_token(refresh_token, ex_user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@users_router.post("/logout", response_model=Dict)
async def logout_user(
        refresh_data: RefreshTokenRequest,
        user_service: UserService = Depends(get_user_service)
):
    """выходим из системы"""
    await user_service.delete_refresh_token(refresh_data.refresh_token)
    return {"details": f"Юзер вышел из системы"}

@users_router.post("/refresh", response_model=TokenResponse)
async def refresh_user(
        refresh_data: RefreshTokenRequest,
        user_service: UserService = Depends(get_user_service)
):
    """просим новые токены"""
    active_session=await user_service.update_refresh_token(refresh_data.refresh_token)
    if not active_session:
        raise HTTPException(status_code=401, detail="токен недействителен")
    user_id = decode_token(active_session.refresh_token, expected_type='refresh')
    if not user_id:
        raise HTTPException(status_code=401, detail="токен просрочен")

    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    await user_service.save_refresh_token(new_refresh_token, user_id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )

