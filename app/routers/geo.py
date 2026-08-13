from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException

from app.dependencies import get_geo_service, get_current_user
from app.models import User
from app.schemas import Coordinates, GeoCreate, GeoRead
from app.geo_service import GeoService

"""роутер нашего сервиса-локатор"""
geo_router = APIRouter(prefix = "/geo", tags = ["Локатор"])

@geo_router.get("/get_country", response_model=GeoRead)
async def get_country(
        coords: Coordinates = Query(...),   # берем из параметров (которые после ? в строке запроса)
        geo_service: GeoService = Depends(get_geo_service),  # сначала найдем сервис (прежде чем выполнять код)
        user:User = Depends(get_current_user)   # ищем юзера, который прислал запрос при помощи access токена
        ):
    """ищем страну по координатам пользователя"""
    try:
        result = geo_service.get_location(coords)
        if not result:
            raise HTTPException(404, detail = "По заданным координатам ничего не найдено")
        record = GeoCreate(
            lat=coords.lat,
            lon=coords.lon,
            user_id=user.id,
            country=result
        )
        new_record=await geo_service.save_record(record)
        # результат формируем из новой записи
        return new_record

    except Exception as e:
        raise HTTPException(500, detail = f'Внутренняя ошибка сервиса: {str(e)}')

@geo_router.get("/get_history", response_model=List[GeoRead])
async def get_history(
        geo_service: GeoService = Depends(get_geo_service),  # сначала найдем сервис (прежде чем выполнять код)
        user: User = Depends(get_current_user)
):
    result = await geo_service.get_history(user)
    return result