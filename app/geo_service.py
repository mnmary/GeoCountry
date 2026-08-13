from typing import Optional, Sequence

from geopy import Nominatim
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.enums import UserRole
from app.models import User, GeoRecord
from app.schemas import Coordinates, GeoCreate


class GeoService:
    """класс - сервис"""
    def __init__(self, db: AsyncSession):
        """инициализация - подключаем локатор"""
        self.db = db
        self.geolocator = Nominatim(user_agent="geo_country_service_v2")

    def _fetch_country(self, coords: Coordinates) -> Optional[str]:
        """Запрос по API к серверу"""
        try:
            location = self.geolocator.reverse((coords.lat, coords.lon), language="en")
            if location and "address" in location.raw:
                return location.raw["address"].get("country")
            return None
        except Exception as e:
            raise RuntimeError(f'Ошибка внешнего локатора: {str(e)}')

    def get_location(self, coords:Coordinates) -> Optional[str]:
        """
        поиск данных по запросу пользователя
        вероятно можем и не найти
        """
        return self._fetch_country(coords)

    async def save_record(self, record: GeoCreate) -> GeoRecord:
        """сохраняем запись"""
        new_record = GeoRecord(
            lat=record.lat,
            lon=record.lon,
            country=record.country,
            user_id=record.user_id,
        )
        self.db.add(new_record)
        await self.db.commit()
        await self.db.refresh(new_record)
        return new_record

    async def get_history(self, current_user: User) -> Sequence[GeoRecord]:
        """выборка записей локатора. Для админа доступны все записи, для юзера - только свои"""
        if current_user.role == UserRole.ADMIN:
            query = select(GeoRecord).options(joinedload(GeoRecord.owner))
        else:
            query = select(GeoRecord).where(GeoRecord.user_id == current_user.id).options(joinedload(GeoRecord.owner))
        result = await self.db.execute(query)
        records = result.scalars().all()
        return records

