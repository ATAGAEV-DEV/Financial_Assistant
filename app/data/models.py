import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SCHEMA = "public"


def get_engine(schema: str) -> AsyncEngine:
    """Создаёт и возвращает асинхронный движок SQLAlchemy с указанным схемой.

    Устанавливает параметр search_path в соединении, чтобы все запросы выполнялись
    в заданной схеме PostgreSQL.

    Args:
        schema (str): Название схемы в базе данных.

    Returns:
        AsyncEngine: Асинхронный движок SQLAlchemy.

    """
    return create_async_engine(
        DATABASE_URL, connect_args={"server_settings": {"search_path": schema}}
    )


if SCHEMA is None or SCHEMA == "":
    engine = get_engine("public")
else:
    engine = get_engine(SCHEMA)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy с поддержкой асинхронности.

    Наследуется от AsyncAttrs и DeclarativeBase, обеспечивая совместимость
    с асинхронным режимом работы SQLAlchemy.
    """

    pass


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
    created_at = Column(DateTime, default=datetime.now)


async def init_models() -> None:
    """Инициализирует модели базы данных.

    Создаёт таблицы в базе данных, если они ещё не существуют.
    Использует метаданные Base для синхронизации схемы.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
