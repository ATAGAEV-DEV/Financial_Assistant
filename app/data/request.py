import asyncio
import json
from datetime import datetime

from sqlalchemy import select

from app.data.models import UserQuery, Users, async_session


DB_TIMEOUT = 10


async def get_user_by_id(user_id: int):
    """Получает пользователя из базы данных по его идентификатору.

    Выполняет асинхронный запрос к базе данных для поиска записи в таблице 'users'
    с указанным user_id. Возвращает объект пользователя или None, если пользователь
    не найден. В случае ошибки выводит сообщение об ошибке и возвращает None.

    Args:
        user_id (int): Уникальный идентификатор пользователя в Telegram.

    Returns:
        Users | None: Объект пользователя, если найден, иначе None.

    """
    try:
        async with async_session() as session:
            query = select(Users).where(Users.user_id == user_id)
            result = await asyncio.wait_for(session.execute(query), timeout=DB_TIMEOUT)
            return result.scalar_one_or_none()
    except asyncio.TimeoutError:
        print(f"Таймаут при получении пользователя с user_id={user_id}")
        return None
    except Exception as e:
        print(f"Ошибка получения пользователя: {e}")
        return None


async def add_user(user_id: int, username: str):
    """Добавляет нового пользователя в базу данных.

    Создаёт и сохраняет новую запись в таблице 'users' с указанными user_id и username.
    В случае ошибки выводит сообщение об ошибке.

    Args:
        user_id (int): Уникальный идентификатор пользователя в Telegram.
        username (str): Имя пользователя в Telegram (может быть пустым).

    """
    try:
        async with async_session() as session:
            user = Users(user_id=user_id, username=username)
            session.add(user)
            await asyncio.wait_for(session.commit(), timeout=DB_TIMEOUT)
    except asyncio.TimeoutError:
        print(f"Таймаут при добавлении пользователя с user_id={user_id}")
    except Exception as e:
        print(f"Ошибка добавления пользователя: {e}")


async def save_user_query(user_id: int, csv_data: list, ai_response: str):
    """Сохраняет запрос пользователя и ответ ИИ в базу данных.

    Args:
        user_id (int): ID пользователя
        csv_data (list): Список словарей с данными CSV
        ai_response (str): Ответ от ИИ

    """
    try:
        async with async_session() as session:
            user_query = UserQuery(
                user_id=user_id,
                csv_data=json.dumps(csv_data, ensure_ascii=False),
                ai_response=ai_response,
                created_at=datetime.now(),
            )
            session.add(user_query)
            await asyncio.wait_for(session.commit(), timeout=DB_TIMEOUT)
    except asyncio.TimeoutError:
        print(f"Таймаут при сохранении запроса пользователя с user_id={user_id}")
    except Exception as e:
        print(f"Ошибка сохранения запроса пользователя: {e}")
