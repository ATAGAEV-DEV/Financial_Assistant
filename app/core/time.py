from datetime import datetime, timezone

import pytz

BUSINESS_TIMEZONE = pytz.timezone("Europe/Moscow")


def business_now() -> datetime:
    """Возвращает текущее время для финансовой логики."""
    return datetime.now(BUSINESS_TIMEZONE)


def utc_now_naive() -> datetime:
    """Возвращает текущее UTC-время без tzinfo для текущей схемы БД."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
