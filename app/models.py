
"""модели для БД"""
from datetime import datetime, timezone
from typing import List

from sqlalchemy import String, Integer, Enum, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column

from app.database import Base
from app.enums import UserRole

"""таблица пользователей"""
class User(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email:Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password:Mapped[str] = mapped_column(String, nullable=False)
    role:Mapped[UserRole] = mapped_column(String, default=UserRole.USER, nullable=False)

    # юзер является владельцем записей в БД
    # GeoRecord.owner
    records:Mapped[List[GeoRecord]] = relationship(back_populates="owner", cascade="all, delete-orphan")

class GeoRecord(Base):
    __tablename__ = "geo_records"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lat:Mapped[float] = mapped_column(Float, nullable=False)
    lon:Mapped[float] = mapped_column(Float, nullable=False)
    country:Mapped[str] = mapped_column(String, nullable=True)
    user_id:Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # User.records
    owner:Mapped[User] = relationship(back_populates="records")

def get_naive_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class UserSession(Base):
    __tablename__ = "user_sessions"
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id:Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token:Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    created_at:Mapped[datetime] = mapped_column(DateTime, nullable=False, default=get_naive_utc_now())
    expires_at:Mapped[datetime] = mapped_column(DateTime, nullable=False)
