import unittest
from datetime import datetime
from io import StringIO
from unittest.mock import patch

from app.core import pandas_parses
from app.core.pandas_parses import csv_to_dict


class CategoryFormattingTests(unittest.TestCase):
    """Test category and month formatting helpers."""

    def test_format_categories_for_empty_set(self) -> None:
        """An empty category set produces an empty string."""
        self.assertEqual(pandas_parses._format_categories(set()), "")

    def test_format_categories_for_one_category(self) -> None:
        """One category is returned without a conjunction."""
        self.assertEqual(pandas_parses._format_categories({"Еда"}), "Еда")

    def test_format_categories_for_two_categories(self) -> None:
        """Two categories are joined with the Russian conjunction."""
        self.assertEqual(pandas_parses._format_categories({"Еда", "Кафе"}), "Еда и Кафе")

    def test_month_genitive_fallback(self) -> None:
        """Unknown month numbers are returned as strings."""
        self.assertEqual(pandas_parses._month_genitive(13), "13")


class CsvReportTests(unittest.TestCase):
    """Test CSV filtering and report branches."""

    @staticmethod
    def _csv(content: str) -> StringIO:
        return StringIO(content)

    def test_empty_current_month_returns_no_data(self) -> None:
        """Rows outside the current month produce an empty report."""
        report, data = csv_to_dict(
            self._csv("date,category,amount\n01/10/2026,Еда,100\n"),
            datetime(2026, 11, 4),
        )

        self.assertEqual(report, "Нет данных о расходах за текущий месяц.")
        self.assertEqual(data, [])

    def test_reserve_overflow_and_zero_spending_days_are_reported(self) -> None:
        """Reserve overflow and excessive daily spending appear in the report."""
        report, data = csv_to_dict(
            self._csv("date,category,amount\n04/11/2026,Машина,21000\n"),
            datetime(2026, 11, 4),
        )

        self.assertIn("Резерв полностью исчерпан и превышен", report)
        self.assertEqual(data[0]["amount"], 21000)

    def test_recommendation_limit_and_overspending_branches(self) -> None:
        """The capped recommendation and zero-spending warning are generated."""
        report, _ = csv_to_dict(
            self._csv("date,category,amount\n20/11/2026,Еда,29000\n"),
            datetime(2026, 11, 20),
        )

        self.assertIn("тебе теперь можно тратить в среднем 91 рублей в день", report)
        self.assertIn("тебе необходимо", report)

    def test_month_name_fallback_and_zero_remaining_days(self) -> None:
        """Fallback month text and a zero-day remainder are handled."""
        current_date = datetime(2026, 11, 4)
        with (
            patch.dict(pandas_parses.MONTH_NAMES, {}, clear=True),
            patch("app.core.pandas_parses.monthrange", return_value=(0, 3)),
        ):
            report, _ = csv_to_dict(
                self._csv("date,category,amount\n04/11/2026,Еда,100\n"),
                current_date,
            )

        self.assertIn("Сейчас идет финансовый месяц: 11.", report)
        self.assertIn("До конца периода осталось 0 дней", report)

    def test_invalid_csv_returns_error_report(self) -> None:
        """Malformed CSV input is converted to a user-facing error."""
        with patch("builtins.print") as print_mock:
            report, data = csv_to_dict(self._csv("invalid\nvalue\n"), datetime(2026, 11, 4))

        self.assertTrue(report.startswith("Ошибка обработки файла:"))
        self.assertEqual(data, [])
        print_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
