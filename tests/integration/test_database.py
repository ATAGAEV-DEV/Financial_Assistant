import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Resolve the test configuration independently of the current working directory.
load_dotenv(Path(__file__).resolve().parents[2] / ".env.test", override=False)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
DATABASE_URL = TEST_DATABASE_URL or ""
request_module: Any = None
Base: Any = None
UserQuery: Any = None
save_user_query: Any = None

if TEST_DATABASE_URL:
    # Keep the application database URL scoped to this test process.
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    from app.data import request as imported_request
    from app.data.models import Base as imported_base
    from app.data.models import UserQuery as imported_user_query
    from app.data.request import save_user_query as imported_save_user_query

    request_module = imported_request
    Base = imported_base
    UserQuery = imported_user_query
    save_user_query = imported_save_user_query


@unittest.skipUnless(TEST_DATABASE_URL, "TEST_DATABASE_URL is required")
class DatabaseIntegrationTests(unittest.IsolatedAsyncioTestCase):
    """Integration tests that use an isolated schema in the test PostgreSQL database."""

    test_user_id = 2_000_000_000 + (os.getpid() % 100_000)

    async def asyncSetUp(self) -> None:
        """Create an isolated schema and route requests to its session."""
        self.schema_name = f"it_financial_assistant_{uuid.uuid4().hex}"
        self.admin_engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
        self.test_engine = create_async_engine(
            DATABASE_URL,
            connect_args={"server_settings": {"search_path": self.schema_name}},
            poolclass=NullPool,
        )

        async with self.admin_engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{self.schema_name}"'))

        async with self.test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        self.original_session_maker = request_module.async_session_maker
        test_session_maker = async_sessionmaker(self.test_engine)
        request_module.async_session_maker = test_session_maker

    async def asyncTearDown(self) -> None:
        """Restore the application session and remove the isolated schema."""
        request_module.async_session_maker = self.original_session_maker

        await self.test_engine.dispose()
        async with self.admin_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{self.schema_name}" CASCADE'))
        await self.admin_engine.dispose()

    async def _query_rows(self) -> list[Any]:
        async with AsyncSession(self.test_engine) as session:
            result = await session.execute(
                select(UserQuery)
                .where(UserQuery.user_id == self.test_user_id)
                .order_by(UserQuery.id)
            )
            return list(result.scalars())

    async def test_created_at_column_is_timestamp_without_timezone(self) -> None:
        """The created_at column remains compatible with the existing schema."""
        async with AsyncSession(self.test_engine) as session:
            result = await session.execute(
                text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_schema = :schema_name
                      AND table_name = 'user_queries'
                      AND column_name = 'created_at'
                    """
                ),
                {"schema_name": self.schema_name},
            )

        self.assertEqual(result.scalar_one(), "timestamp without time zone")

    async def test_save_user_query_persists_naive_utc_timestamp(self) -> None:
        """Saving a query stores one response with a naive UTC timestamp."""
        await save_user_query(
            self.test_user_id,
            [{"date": "2026-11-04", "category": "Еда", "amount": 350}],
            "integration response",
        )

        rows = await self._query_rows()

        self.assertEqual(len(rows), 1)
        current_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        for row in rows:
            self.assertEqual(row.ai_response, "integration response")
            self.assertIsNotNone(row.created_at)
            self.assertIsNone(row.created_at.tzinfo)
            self.assertLess(abs(row.created_at - current_utc), timedelta(seconds=30))

    async def test_user_query_model_default_is_naive_utc(self) -> None:
        """The model default stores a naive UTC timestamp."""
        async with AsyncSession(self.test_engine) as session:
            session.add(
                UserQuery(
                    user_id=self.test_user_id,
                    csv_data="[]",
                    ai_response="model default",
                )
            )
            await session.commit()

        rows = await self._query_rows()

        self.assertEqual(len(rows), 1)
        self.assertIsNotNone(rows[0].created_at)
        self.assertIsNone(rows[0].created_at.tzinfo)


if __name__ == "__main__":
    unittest.main()
