from sqlalchemy import Enum

"""Роли пользователей"""
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

    # Добавим этот метод, чтобы Pydantic 2.x на Python 3.14 гарантированно понимал, как валидировать этот тип
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.str_schema()