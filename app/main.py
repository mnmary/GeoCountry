from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from sqlalchemy import select
from starlette.middleware.cors import CORSMiddleware

from app.config import config
from app.database import engine, Base, AsyncSessionLocal
from app.enums import UserRole
from app.models import User
from app.routers.geo import geo_router

from app.routers.users import users_router

"""главный модуль - точка входа"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Асинхронно создаем таблицы в Postgres при старте
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # создаем админа со всеми правами
    async with AsyncSessionLocal() as db:
        query = select(User).where(User.email == config.ADMIN_EMAIL)
        result = await db.execute(query)
        user = result.scalars().one_or_none()
        if not user:
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(config.ADMIN_PASSWORD.encode('utf-8'), salt).decode('utf-8')
            user = User(email=config.ADMIN_EMAIL, hashed_password=hashed_password, role=UserRole.ADMIN)
            db.add(user)
            await db.commit()
            print("admin is added to database")
    yield
    # Здесь закрываем движок при выключении сервера
    await engine.dispose()
geo_app = FastAPI(title = "Геосервис", lifespan=lifespan)  # приложение

'''CORS'''
geo_app.add_middleware(
    CORSMiddleware,
    # allow_origins — список сайтов, которым разрешено делать запросы к нашему API.
    # Значение ["*"] разрешает доступ абсолютно всем (идеально для локальной разработки и файлов file://)
    allow_origins=["*"],

    # allow_credentials=True разрешает передавать куки и заголовки авторизации (наш Bearer токен)
    allow_credentials=True,

    # allow_methods — список разрешенных HTTP-методов. ["*"] разрешает GET, POST, PUT, DELETE и т.д.
    allow_methods=["*"],

    # allow_headers — список разрешенных заголовков запроса. ["*"] разрешает любые заголовки,
    # что важно для нашего кастомного заголовка "Authorization"
    allow_headers=["*"],
)
geo_app.include_router(geo_router)  # роутер локатора
geo_app.include_router(users_router)    # роутер сервиса пользователей

"""роутинг"""
@geo_app.get("/")
async def read_root() -> dict:
    """
    Точка входа сервиса
    :return: сообщение
    """
    return {"message": f"Геосервис запущен!"}