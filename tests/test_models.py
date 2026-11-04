import os
import runpy
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")

from app.data import models


class ModelsTests(unittest.IsolatedAsyncioTestCase):
    """Test SQLAlchemy model setup without opening a real database connection."""

    async def test_init_models_creates_tables(self) -> None:
        """Model initialization creates all metadata tables."""
        connection = MagicMock()
        connection.run_sync = AsyncMock()
        engine_context = MagicMock()
        engine_context.__aenter__ = AsyncMock(return_value=connection)
        engine_context.__aexit__ = AsyncMock(return_value=None)
        engine = MagicMock()
        engine.begin.return_value = engine_context
        with patch.object(models, "engine", engine):
            await models.init_models()

        engine.begin.assert_called_once()
        connection.run_sync.assert_awaited_once_with(models.Base.metadata.create_all)

    def test_missing_database_url_raises_clear_error(self) -> None:
        """Importing models without DATABASE_URL raises a clear error."""
        models_path = Path(__file__).parents[1] / "app" / "data" / "models.py"
        database_url = os.environ.pop("DATABASE_URL", None)
        try:
            with (
                patch("dotenv.load_dotenv"),
                self.assertRaisesRegex(RuntimeError, "DATABASE_URL не задан"),
            ):
                runpy.run_path(str(models_path), run_name="isolated_models_import")
        finally:
            if database_url is not None:
                os.environ["DATABASE_URL"] = database_url


if __name__ == "__main__":
    unittest.main()
