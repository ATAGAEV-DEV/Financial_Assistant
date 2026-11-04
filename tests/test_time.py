import unittest
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

from app.core.pandas_parses import csv_to_dict
from app.core.time import BUSINESS_TIMEZONE, business_now, utc_now_naive


class TimeHelpersTests(unittest.TestCase):
    @patch("app.core.time.datetime")
    def test_business_now_uses_business_timezone(self, datetime_mock) -> None:
        expected = datetime(2026, 11, 4, 1, 0, tzinfo=BUSINESS_TIMEZONE)
        datetime_mock.now.return_value = expected

        result = business_now()

        self.assertEqual(result, expected)
        datetime_mock.now.assert_called_once_with(BUSINESS_TIMEZONE)

    @patch("app.core.time.datetime")
    def test_utc_now_naive_returns_naive_utc_datetime(self, datetime_mock) -> None:
        expected_utc = datetime(2026, 11, 3, 22, 0, tzinfo=timezone.utc)
        datetime_mock.now.return_value = expected_utc

        result = utc_now_naive()

        self.assertEqual(result, expected_utc.replace(tzinfo=None))
        self.assertIsNone(result.tzinfo)
        datetime_mock.now.assert_called_once_with(timezone.utc)


class CsvTimezoneRegressionTests(unittest.TestCase):
    def test_report_uses_moscow_date_at_utc_previous_day(self) -> None:
        utc_moment = datetime(2026, 11, 3, 22, 0, tzinfo=timezone.utc)
        moscow_moment = utc_moment.astimezone(BUSINESS_TIMEZONE)
        csv_file = StringIO("date,category,amount\n04/11/2026,Еда,350\n")

        report, csv_data = csv_to_dict(csv_file, moscow_moment)

        self.assertIn("4 ноября 2026 года", report)
        self.assertEqual(csv_data[0]["date"], "2026-11-04")


if __name__ == "__main__":
    unittest.main()
