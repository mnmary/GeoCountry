"""сервис для работы с юзерами"""
from datetime import timedelta, timezone, datetime

import jwt
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.models import User, UserSession
from app.schemas import UserCreate
import bcrypt

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, payload: UserCreate) -> User:
        hashed_password = self._hash_password(payload.password)
        new_user = User(
            email=str(payload.email),
            hashed_password=hashed_password
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    @staticmethod
    def _hash_password(payload:str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(payload.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    async def get_user_by_email(self, email:str) -> User:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    def verify_password(password:str, hash_password:str) -> bool:
        try:
            password_bytes = password.encode('utf-8')
            hash_password_bytes = hash_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_password_bytes)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def create_access_token(user_id:int) -> str:
        expires = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            'exp': expires,
            'sub': user_id,
            'type': 'access'
        }
        return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id:int) -> str:
        expires = datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            'exp': expires,
            'sub': user_id,
            'type': 'refresh'
        }
        return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token:str, expected_type:str) -> int| None:
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=config.JWT_ALGORITHM, options={"verify_exp": True} )
            print(payload)
            if payload.get('type') != expected_type:
                return None
            return payload.get('sub')   # user id
        except Exception as e:
            print(str(e))
            return None

    async def save_refresh_token(self, refresh_token:str, user_id:int) -> None:
        """создаем новую сессию с токеном"""
        try:
            payload = jwt.decode(refresh_token, config.SECRET_KEY, algorithms=config.JWT_ALGORITHM)
            exp_timestamp = payload.get('exp')
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        except:
            expires_at = datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)

        # Убираем таймзону для совместимости с базой данных
        expires_at_naive = expires_at.replace(tzinfo=None)

        session = UserSession(
            expires_at=expires_at_naive,
            user_id = user_id,
            refresh_token = refresh_token
        )
        self.db.add(session)
        await self.db.commit()
        return None

    async def update_refresh_token(self, old_token:str) -> UserSession|None:
        query = select(UserSession).where(UserSession.refresh_token == old_token)
        result = await self.db.execute(query)
        record = result.scalar_one_or_none()
        if record:
            await self.db.delete(record)
            await self.db.commit()
            return record
        return None

    async def delete_refresh_token(self, refresh_token:str) -> None:
        query = delete(UserSession).where(UserSession.refresh_token == refresh_token)
        await self.db.execute(query)
        return None