from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.core.generate import ai_generate
from app.core.pandas_parses import csv_to_dict
from app.data.request import add_user, get_user_by_id, save_user_query
from app.tools.utils import hash_password

router = Router()


ACCESS_PASSWORD = "e5ae93bd8095fbd86c25a110bbf194a5a1a209f1e8eb31bb30c8b0ecbe254d58"


class RegisterState(StatesGroup):
    """Группа состояний для процесса регистрации пользователя.

    Содержит состояния, используемые в конечном автомате (FSM) при авторизации.
    """

    waiting_for_password = State()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start.

    Проверяет, существует ли пользователь в базе данных.
    Если существует — приветствует. Если нет — запрашивает пароль доступа
    и переводит пользователя в состояние ожидания ввода пароля.

    Args:
        message (Message): Объект входящего сообщения от пользователя.
        state (FSMContext): Контекст состояния конечного автомата.

    """
    user_id = message.from_user.id
    user = await get_user_by_id(user_id)
    if user:
        await message.answer(
            "Добро пожаловать!\n"
            " Пожалуйста, пришлите файл в формате CSV с полями: date, category, amount."
        )
    else:
        await message.answer("Добро пожаловать! Для продолжения работы введите пароль для доступа.")
        await state.set_state(RegisterState.waiting_for_password)


@router.message(RegisterState.waiting_for_password)
async def password_handler(message: Message, state: FSMContext) -> None:
    """Обработчик ввода пароля при регистрации.

    Проверяет хешированный ввод пользователя на соответствие
    заранее заданному хешу ACCESS_PASSWORD. При успехе — добавляет
    пользователя в базу данных, отправляет подтверждение и очищает состояние.
    Иначе — запрашивает ввод пароля повторно.

    Args:
        message (Message): Сообщение с введённым паролем.
        state (FSMContext): Контекст состояния конечного автомата.

    """
    user_id = message.from_user.id
    if hash_password(message.text.strip()) == ACCESS_PASSWORD:
        await add_user(user_id, message.from_user.username or "")
        await message.answer("Авторизация успешна! Теперь у вас полный доступ.")
        await state.clear()
    else:
        await message.answer("Неверный пароль. Попробуйте еще раз:")


@router.message(lambda message: message.document and message.document.file_name.endswith(".csv"))
async def handle_csv_file(message: Message) -> None:
    """Обработчик CSV-файлов.

    Args:
        message (Message): Сообщение с прикрепленным CSV-файлом.

    """
    document = message.document
    file = await message.bot.download(document.file_id)

    try:
        result = csv_to_dict(file)
        if not result:
            await message.answer("Файл пуст или содержит некорректные данные.")
            return

        response = await ai_generate(result)
        await save_user_query(user_id=message.from_user.id, csv_data=result, ai_response=response)

        await message.answer(response)
    except Exception as e:
        await message.answer(f"Ошибка обработки файла: {str(e)}")

    finally:
        file.close()
