import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")

from app.core import handlers


class HandlerTests(unittest.IsolatedAsyncioTestCase):
    """Test Telegram handlers without contacting Telegram or PostgreSQL."""

    @staticmethod
    def _message(user_id: int = 42, username: str | None = "tester") -> MagicMock:
        message = MagicMock()
        message.from_user = SimpleNamespace(id=user_id, username=username)
        message.answer = AsyncMock()
        return message

    @staticmethod
    def _state() -> MagicMock:
        state = MagicMock()
        state.set_state = AsyncMock()
        state.clear = AsyncMock()
        return state

    async def test_start_handler_greets_existing_user(self) -> None:
        """Existing users receive the file instructions."""
        message = self._message()
        state = self._state()
        with patch.object(handlers, "get_user_by_id", new=AsyncMock(return_value=object())):
            await handlers.start_handler(message, state)

        message.answer.assert_awaited_once()
        state.set_state.assert_not_awaited()

    async def test_start_handler_starts_registration_for_new_user(self) -> None:
        """Unknown users are moved to the password state."""
        message = self._message()
        state = self._state()
        with patch.object(handlers, "get_user_by_id", new=AsyncMock(return_value=None)):
            await handlers.start_handler(message, state)

        state.set_state.assert_awaited_once_with(handlers.RegisterState.waiting_for_password)
        message.answer.assert_awaited_once_with(
            "Добро пожаловать! Для продолжения работы введите пароль для доступа."
        )

    async def test_password_handler_authorizes_valid_password(self) -> None:
        """A valid password creates the user and clears the state."""
        message = self._message(username=None)
        message.text = "valid password"
        state = self._state()
        add_user = AsyncMock()
        with (
            patch.object(handlers, "hash_password", return_value=handlers.ACCESS_PASSWORD),
            patch.object(handlers, "add_user", new=add_user),
        ):
            await handlers.password_handler(message, state)

        add_user.assert_awaited_once_with(42, "")
        state.clear.assert_awaited_once()
        message.answer.assert_awaited_once_with("Авторизация успешна! Теперь у вас полный доступ.")

    async def test_password_handler_rejects_invalid_password(self) -> None:
        """An invalid password leaves the user in the current state."""
        message = self._message()
        message.text = "invalid password"
        state = self._state()
        add_user = AsyncMock()
        with (
            patch.object(handlers, "hash_password", return_value="wrong"),
            patch.object(handlers, "add_user", new=add_user),
        ):
            await handlers.password_handler(message, state)

        add_user.assert_not_awaited()
        state.clear.assert_not_awaited()
        message.answer.assert_awaited_once_with("Неверный пароль. Попробуйте еще раз:")

    async def test_handle_csv_file_saves_and_sends_report(self) -> None:
        """A valid CSV is saved and its report is sent to the user."""
        message = self._message()
        message.document = SimpleNamespace(file_id="file-id")
        message.bot = MagicMock()
        downloaded_file = MagicMock()
        message.bot.download = AsyncMock(return_value=downloaded_file)
        save_user_query = AsyncMock()
        with (
            patch.object(handlers, "business_now", return_value=datetime(2026, 11, 4)),
            patch.object(handlers, "csv_to_dict", return_value=("report", [{"amount": 1}])),
            patch.object(handlers, "save_user_query", new=save_user_query),
        ):
            await handlers.handle_csv_file(message)

        save_user_query.assert_awaited_once_with(42, [{"amount": 1}], "report")
        message.answer.assert_awaited_once_with("report")
        downloaded_file.close.assert_called_once()

    async def test_handle_csv_file_reports_empty_file(self) -> None:
        """An empty report is returned to the user without a database write."""
        message = self._message()
        message.document = SimpleNamespace(file_id="file-id")
        message.bot = MagicMock()
        downloaded_file = MagicMock()
        message.bot.download = AsyncMock(return_value=downloaded_file)
        save_user_query = AsyncMock()
        with (
            patch.object(handlers, "csv_to_dict", return_value=("", [])),
            patch.object(handlers, "save_user_query", new=save_user_query),
        ):
            await handlers.handle_csv_file(message)

        save_user_query.assert_not_awaited()
        message.answer.assert_awaited_once_with("Файл пуст или содержит некорректные данные.")
        downloaded_file.close.assert_called_once()

    async def test_handle_csv_file_reports_processing_error(self) -> None:
        """Processing failures are converted to an error message."""
        message = self._message()
        message.document = SimpleNamespace(file_id="file-id")
        message.bot = MagicMock()
        downloaded_file = MagicMock()
        message.bot.download = AsyncMock(return_value=downloaded_file)
        with patch.object(handlers, "csv_to_dict", side_effect=ValueError("bad csv")):
            await handlers.handle_csv_file(message)

        message.answer.assert_awaited_once_with("Ошибка обработки файла: bad csv")
        downloaded_file.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
