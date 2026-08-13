from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import config

"""движок базы данных"""
engine = create_async_engine(config.DATABASE_URL)

"""Создаем фабрику асинхронных сессий SQLAlchemy 2.0!"""
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)
"""Базовый класс SQLAlchemy 2.0!"""
# от него пойдут все наши модели БД
class Base(DeclarativeBase):
    pass