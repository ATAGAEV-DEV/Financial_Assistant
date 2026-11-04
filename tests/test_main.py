import asyncio
import os
import runpy
import unittest
from collections.abc import Coroutine
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")
os.environ.setdefault("TG_TOKEN", "test-token")

import main as main_module


class MainTests(unittest.IsolatedAsyncioTestCase):
    """Test bot startup orchestration without starting polling."""

    async def test_main_initializes_database_and_starts_polling(self) -> None:
        """The main coroutine initializes dependencies and starts polling."""
        bot = MagicMock()
        dispatcher = MagicMock()
        dispatcher.start_polling = AsyncMock()
        init_models = AsyncMock()
        with (
            patch.object(main_module, "Bot", return_value=bot) as bot_class,
            patch.object(main_module, "Dispatcher", return_value=dispatcher),
            patch.object(main_module, "init_models", new=init_models),
        ):
            await main_module.main()

        bot_class.assert_called_once_with(token=main_module.TG_TOKEN)
        dispatcher.include_router.assert_called_once_with(main_module.router)
        init_models.assert_awaited_once()
        dispatcher.start_polling.assert_awaited_once_with(bot)

    def test_module_entrypoint_invokes_asyncio_run(self) -> None:
        """Running main.py as a script invokes asyncio.run."""
        main_path = Path(__file__).parents[1] / "main.py"

        def close_coroutine(coroutine: Coroutine[Any, Any, Any]) -> None:
            coroutine.close()

        with patch.object(asyncio, "run", side_effect=close_coroutine) as run_mock:
            runpy.run_path(str(main_path), run_name="__main__")

        run_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
