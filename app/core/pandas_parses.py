from calendar import monthrange
from datetime import datetime
from typing import Any

import pandas as pd

MONTH_NAMES = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}

RESERVE_CATEGORIES = {"Машина", "Лекарство", "Подарки", "Шопинг"}
RESERVE_LIMIT = 20_000
MAIN_BUDGET = 30_000
DAILY_LIMIT = 1_000


def _format_categories(categories: set[str]) -> str:
    """Форматирует множество категорий в строку с правильной русской грамматикой."""
    sorted_cats = sorted(categories)
    if not sorted_cats:
        return ""
    if len(sorted_cats) == 1:
        return sorted_cats[0]
    if len(sorted_cats) == 2:
        return f"{sorted_cats[0]} и {sorted_cats[1]}"
    return ", ".join(sorted_cats[:-1]) + f" и {sorted_cats[-1]}"


def csv_to_dict(csv_file: Any, current_date: datetime) -> tuple[str, list[dict]]:
    """Преобразует CSV-файл в текстовый отчёт о расходах за текущий месяц."""
    try:
        df = pd.read_csv(csv_file, encoding="utf-8", delimiter=",")
        df = df[["date", "category", "amount"]]
        df["date"] = pd.to_datetime(df["date"], dayfirst=True)

        filter_date = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        df = df[df["date"].dt.normalize() >= pd.Timestamp(filter_date.date())]
        df["amount"] = df["amount"].astype(str).str.replace(r"[^\d.]", "", regex=True)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df = df[df["category"] != "Зарплата"]
        df = df.dropna(subset=["amount"])

        if df.empty:
            return "Нет данных о расходах за текущий месяц.", []

        day = current_date.day
        month_name_gen = _month_genitive(current_date.month)
        year = current_date.year
        date_str = f"{day} {month_name_gen} {year} года"

        month_name = MONTH_NAMES.get(current_date.month, str(current_date.month))

        total_amount = int(df["amount"].sum())

        category_sum = df.groupby("category")["amount"].sum().sort_values(ascending=False)

        reserve_spent = int(df[df["category"].isin(RESERVE_CATEGORIES)]["amount"].sum())
        main_spent = total_amount - reserve_spent
        main_left = MAIN_BUDGET - main_spent

        reserve_diff = RESERVE_LIMIT - reserve_spent
        reserve_spent_fmt = f"{reserve_spent:,}".replace(",", " ")
        categories_str = _format_categories(RESERVE_CATEGORIES)
        reserve_limit_str = f"{RESERVE_LIMIT:,}".replace(",", " ")
        main_budget_str = f"{MAIN_BUDGET:,}".replace(",", " ")
        daily_limit_str = f"{DAILY_LIMIT:,}".replace(",", " ")
        if reserve_diff >= 0:
            reserve_diff_fmt = f"{reserve_diff:,}".replace(",", " ")
            reserve_line = (
                f"Из резерва ({reserve_limit_str} руб.) на категории {categories_str} потрачено: "
                f"{reserve_spent_fmt} руб. Остаток резерва: {reserve_diff_fmt} руб."
            )
        else:
            reserve_over_fmt = f"{abs(reserve_diff):,}".replace(",", " ")
            reserve_line = (
                f"Из резерва ({reserve_limit_str} руб.) на категории {categories_str} потрачено: "
                f"{reserve_spent_fmt} руб. Резерв полностью исчерпан"
                f" и превышен на {reserve_over_fmt} руб."
            )

        days_in_month = monthrange(current_date.year, current_date.month)[1]
        days_left = days_in_month - current_date.day + 1

        days_passed = current_date.day
        avg_daily_actual = round(main_spent / days_passed)
        recommended_daily = round(max(0, main_left) / days_left) if days_left > 0 else 0
        recommended_daily_capped = min(recommended_daily, DAILY_LIMIT)

        total_amount_fmt = f"{total_amount:,}".replace(",", " ")

        lines = [
            f"Привет! Проанализировал твои траты по состоянию на {date_str}.",
            f"Сейчас идет финансовый месяц: {month_name}.",
            "",
            f"Общие расходы с начала периода: {total_amount_fmt} рублей.",
            "",
            "Основные категории трат:",
        ]

        for category, amount in category_sum.items():
            amount_fmt = f"{int(amount):,}".replace(",", " ")
            lines.append(f"{category}: {amount_fmt} руб.")

        projected_total = round(main_spent / days_passed * days_in_month)
        projected_total_fmt = f"{projected_total:,}".replace(",", " ")

        recommended_daily_fmt = f"{recommended_daily:,}".replace(",", " ")
        recommended_daily_capped_fmt = f"{recommended_daily_capped:,}".replace(",", " ")
        avg_daily_actual_fmt = f"{avg_daily_actual:,}".replace(",", " ")

        if recommended_daily > DAILY_LIMIT:
            recommendation_line = (
                f"Чтобы уложиться в плановый бюджет ({main_budget_str} руб.),"
                f" тебе теперь можно тратить в среднем не более {daily_limit_str} рублей в день"
                f" (расчётный лимит составил бы {recommended_daily_fmt} руб.,"
                f" но мы ограничиваем его {daily_limit_str} руб.)."
            )
        else:
            recommendation_line = (
                f"Чтобы уложиться в плановый бюджет ({main_budget_str} руб.),"
                " тебе теперь можно тратить в среднем"
                f" {recommended_daily_capped_fmt} рублей в день."
            )

        main_spent_fmt = f"{main_spent:,}".replace(",", " ")
        main_left_fmt = f"{main_left:,}".replace(",", " ")

        lines += [
            "",
            "Разделение по бюджетам:",
            reserve_line,
            (
                f"Из основного бюджета ({main_budget_str} руб.) на регулярные нужды потрачено:"
                f" {main_spent_fmt} руб."
            ),
            f"Остаток основного бюджета: {main_left_fmt} руб.",
            f"До конца периода осталось {days_left} дней (включая сегодня).",
            "",
            "Рекомендация по тратам:",
            recommendation_line,
            (
                f"Пока что твои средние фактические дневные траты составляют"
                f" {avg_daily_actual_fmt} рублей"
                f" (из расчета за {days_passed} прошедших дней)."
            ),
            (
                f"Если ты продолжишь тратить в таком же ритме, то к концу"
                f" {month_name_gen} общая сумма расходов составит"
                f" около {projected_total_fmt} рублей."
            ),
        ]

        if avg_daily_actual > DAILY_LIMIT:
            overspend = avg_daily_actual - DAILY_LIMIT
            zero_days = -(-overspend * days_passed // DAILY_LIMIT)
            lines.append(
                f"Так как текущий дневной расход превышает целевой"
                f" (около {daily_limit_str} руб. в день на основной бюджет)"
                f" более чем на {overspend} рублей,"
                f" тебе необходимо {zero_days} дней без трат."
            )

        report = "\n".join(lines)
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        return report, df.to_dict(orient="records")

    except Exception as e:  # noqa: BLE001 - намеренный catch-all для CSV-обработки
        print(f"Ошибка обработки CSV файла: {e}")
        return f"Ошибка обработки файла: {e}", []


def _month_genitive(month: int) -> str:
    """Возвращает название месяца в родительном падеже."""
    genitive = {
        1: "января",
        2: "февраля",
        3: "марта",
        4: "апреля",
        5: "мая",
        6: "июня",
        7: "июля",
        8: "августа",
        9: "сентября",
        10: "октября",
        11: "ноября",
        12: "декабря",
    }
    return genitive.get(month, str(month))
