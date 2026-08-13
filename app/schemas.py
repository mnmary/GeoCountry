from typing import Optional, Self

from pydantic import BaseModel, Field, EmailStr, model_validator

from app.enums import UserRole

"""структуры для валидации входных данных"""
class Coordinates(BaseModel):
    """входные координаты"""
    lat: float = Field(..., ge=-90, le=90, description="Широта")
    lon: float = Field(..., ge=-180, le=180, description="Долгота")

class CountryResponse(BaseModel):
    """выходные данные для пользователя"""
    country: str
    lat: float
    lon: float

"""--- для юзера делаем три схемы: на создание, изменение и чтение ---"""

class UserBase(BaseModel):
    """базовые данные для юзера"""
    email: EmailStr = Field(..., description="Почтовый адрес пользователя (используем как логин)")
    """мы отдаем данные клиенту - это ставить обязательно!"""
    class Config:
        from_attributes = True

class UserCreate(UserBase):
    """данные для регистрации нового юзера"""
    password: str = Field(..., min_length=6, description="Пароль минимум 6 символов")
    password_confirm: str = Field(..., description="Подтверждение пароля")

    """
    объект уже есть, нам надо сверить пароли
    """
    @model_validator(mode="after")
    def validate_password(self) -> Self:
        """вызывается после валидации полей (уже создан объект)"""
        if self.password != self.password_confirm:
            raise ValueError("пароли не совпадают")
        return self

# ! Обратите внимание - наследуемся от BaseModel!
class UserUpdate(BaseModel):
    """данные для обновления юзера"""
    email:Optional[EmailStr] = Field(None, description="Новый почтовый ящик")
    password:Optional[str] = Field(None, description="новый пароль")

class UserRead(UserBase):
    """данные для чтения юзера"""
    id:int
    role:UserRole
    """
    используем только при чтении! 
    чтобы при валидации pydantic читал это как объект (через точку)
    он ведь ждет данные в формате словаря, а мы возвращаем объект!
    """
    class Config:
        from_attributes = True

"""--- для локатора делаем две схемы: на создание и на чтение ---"""

class GeoCreate(BaseModel):
    """для добавления записи локатора в базу"""
    lat: float = Field(..., ge=-90, le=90, description="Широта")
    lon: float = Field(..., ge=-180, le=180, description="Долгота")
    country:str = Field(..., description="Название страны, полученное от Geopy")
    user_id:int = Field(..., description="ID Владельца записи")

class GeoRead(BaseModel):
    """данные для чтения локатора"""
    id: int
    lat: float
    lon: float
    country: str
    user_id: int
    owner: UserMin
    """мы отдаем данные клиенту - это ставить обязательно!"""
    class Config:
        from_attributes = True

class UserMin(BaseModel):
    email: EmailStr
    role: UserRole
    """мы отдаем данные клиенту - это ставить обязательно!"""
    class Config:
        from_attributes = True

# --- СХЕМЫ ДЛЯ АУТЕНТИФИКАЦИИ ---

class TokenResponse(BaseModel):
    """Схема ответа, возвращающая пару токенов."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    """Схема запроса для обновления токенов."""
    refresh_token: str
