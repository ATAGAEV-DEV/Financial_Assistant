import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")

from app.data import request


class _SessionContext:
    """Provide an asynchronous context manager for a fake session."""

    def __init__(self, session: MagicMock) -> None:
        self.session = session

    async def __aenter__(self) -> MagicMock:
        return self.session

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


class RequestTests(unittest.IsolatedAsyncioTestCase):
    """Test database request helpers with mocked SQLAlchemy sessions."""

    @staticmethod
    def _session() -> MagicMock:
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.add = MagicMock()
        return session

    @staticmethod
    def _session_factory(session: MagicMock) -> MagicMock:
        return MagicMock(return_value=_SessionContext(session))

    async def test_get_user_by_id_returns_user(self) -> None:
        """A successful lookup returns the scalar user."""
        session = self._session()
        result = MagicMock()
        user = object()
        result.scalar_one_or_none.return_value = user
        session.execute.return_value = result
        with patch.object(request, "async_session_maker", self._session_factory(session)):
            actual = await request.get_user_by_id(42)

        self.assertIs(actual, user)
        session.execute.assert_awaited_once()

    async def test_get_user_by_id_handles_timeout(self) -> None:
        """A lookup timeout returns None."""
        session = self._session()
        session.execute.side_effect = asyncio.TimeoutError
        with (
            patch.object(request, "async_session_maker", self._session_factory(session)),
            patch("builtins.print") as print_mock,
        ):
            actual = await request.get_user_by_id(42)

        self.assertIsNone(actual)
        print_mock.assert_called_once()

    async def test_get_user_by_id_handles_unexpected_error(self) -> None:
        """An unexpected lookup error returns None."""
        session = self._session()
        session.execute.side_effect = RuntimeError("database unavailable")
        with (
            patch.object(request, "async_session_maker", self._session_factory(session)),
            patch("builtins.print") as print_mock,
        ):
            actual = await request.get_user_by_id(42)

        self.assertIsNone(actual)
        print_mock.assert_called_once()

    async def test_add_user_commits_upsert(self) -> None:
        """A user upsert executes and commits successfully."""
        session = self._session()
        with patch.object(request, "async_session_maker", self._session_factory(session)):
            await request.add_user(42, "tester")

        session.execute.assert_awaited_once()
        session.commit.assert_awaited_once()

    async def test_add_user_handles_timeout(self) -> None:
        """A user upsert timeout is handled without raising."""
        session = self._session()
        session.execute.side_effect = asyncio.TimeoutError
        with (
            patch.object(request, "async_session_maker", self._session_factory(session)),
            patch("builtins.print") as print_mock,
        ):
            await request.add_user(42, "tester")

        print_mock.assert_called_once()

    async def test_add_user_handles_unexpected_error(self) -> None:
        """An unexpected user upsert error is handled without raising."""
        session = self._session()
        session.execute.side_effect = RuntimeError("database unavailable")
        with (
            patch.object(request, "async_session_maker", self._session_factory(session)),
            patch("builtins.print") as print_mock,
        ):
            await request.add_user(42, "tester")

        print_mock.assert_called_once()

    async def test_save_user_query_commits_json_and_timestamp(self) -> None:
        """A query is serialized, added, and committed successfully."""
        session = self._session()
        with patch.object(request, "async_session_maker", self._session_factory(session)):
            await request.save_user_query(42, [{"amount": 350}], "report")

        session.add.assert_called_once()
        saved_query = session.add.call_args.args[0]
        self.assertEqual(saved_query.user_id, 42)
        self.assertEqual(saved_query.csv_data, '[{"amount": 350}]')
        self.assertEqual(saved_query.ai_response, "report")
        self.assertIsNone(saved_query.created_at.tzinfo)
        session.commit.assert_awaited_once()

    async def test_save_user_query_handles_timeout(self) -> None:
        """A query save timeout is handled without raising."""
        session = self._session()
        session.commit.side_effect = asyncio.TimeoutError
        with (
            patch.object(request, "async_session_maker", self._session_factory(session)),
            patch("builtins.print") as print_mock,
        ):
            await request.save_user_query(42, [], "report")

        print_mock.assert_called_once()

    async def test_save_user_query_handles_unexpected_error(self) -> None:
        """An unexpected query save error is handled without raising."""
        session = self._session()
        session.add.side_effect = RuntimeError("database unavailable")
        with (
            patch.object(request, "async_session_maker", self._session_factory(session)),
            patch("builtins.print") as print_mock,
        ):
            await request.save_user_query(42, [], "report")

        print_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
