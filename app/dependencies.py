from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_token
from app.database import AsyncSessionLocal
from app.models import User
from app.geo_service import GeoService
from app.user_service import UserService

"""сессия БД"""
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

"""наш сервис"""
def get_geo_service(db: AsyncSession = Depends(get_db)) -> GeoService:
    return GeoService(db)

"""сервис пользователей"""
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

"""текущий юзер по токену"""
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login") # для Swagger UI (окно авторизации через логин и пароль. Запрос токена производится автоматически по команде tokenURL)
oauth2_scheme = HTTPBearer() # для Swagger UI (окно авторизации с вводом токена)
async def get_current_user(
        db: AsyncSession = Depends(get_db), # сессия БД
        credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme) # токен берется из заголовка Authorization bearer <access token>
) -> User:
    token = credentials.credentials  # уже чистый JWT, без "Bearer "
    # ПРИНТ ДЛЯ ОТЛАДКИ: Посмотрим, что прилетело в token от фронтенда
    print(f"🔑 [БЭКЕНД ДЕБАГ] В get_current_user пришёл токен: {token[:20]}... (длина: {len(token)})")
    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "")

    # Печатаем чистый отладочный принт, чтобы убедиться, что слово "Bearer" ушло
    print(f"🔑 [БЭКЕНД] Чистый токен, готовый к расшифровке: '{token[:20]}...'")

    user_id = decode_token(token, expected_type="access")
    if not user_id:
        raise HTTPException(status_code=401, detail="токен некорректный", headers={"WWW-Authenticate": "Bearer"})

    # 2. Ищем пользователя в базе данных
    query = select(User).where(User.id == user_id)
    user = await db.execute(query)
    result = user.scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=401, detail="юзер не найден", headers={"WWW-Authenticate": "Bearer"})
    return result

