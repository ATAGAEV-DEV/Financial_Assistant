import os

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.time import utc_now_naive

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL не задан в переменных окружения. Установите переменную "
        "для подключения к PostgreSQL."
    )
SCHEMA = "pictures"


def get_engine(schema: str, db_url: str) -> AsyncEngine:
    """Создаёт и возвращает асинхронный движок SQLAlchemy с указанным схемой.

    Устанавливает параметр search_path в соединении, чтобы все запросы выполнялись
    в заданной схеме PostgreSQL.
    """
    return create_async_engine(
        db_url,
        connect_args={"server_settings": {"search_path": schema}},
        pool_pre_ping=True,
        pool_recycle=1800,
    )


engine = get_engine(SCHEMA, DATABASE_URL)
async_session_maker = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy с поддержкой асинхронности.

    Наследуется от AsyncAttrs и DeclarativeBase, обеспечивая совместимость
    с асинхронным режимом работы SQLAlchemy.
    """


class Users(Base):
    """Модель пользователя в базе данных.

    Представляет таблицу 'users', хранящую идентификаторы Telegram-пользователей
    и их имена пользователей.
    """

    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=False)
    username = Column(String)


class UserQuery(Base):
    """Модель для хранения запросов пользователей и ответов ИИ."""

    __tablename__ = "user_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    csv_data = Column(Text, nullable=False)  # JSON в виде строки
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=False), default=utc_now_naive)


async def init_models() -> None:
    """Создает таблицы в базе данных, если они не существуют."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
