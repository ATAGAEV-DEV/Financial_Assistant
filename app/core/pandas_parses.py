from datetime import datetime
from typing import Any

import pandas as pd


def csv_to_dict(csv_file: Any) -> tuple:
    """Преобразует CSV-файл в список словарей с определённой структурой.

    Функция читает CSV-файл, извлекает столбцы 'date', 'category' и 'amount',
    обрабатывает данные: приводит даты к формату YYYY-MM-DD, фильтрует записи,
    оставляя только те, дата которых не раньше 1-го числа текущего месяца,
    очищает и преобразует суммы к числовому типу.
    """
    try:
        df = pd.read_csv(csv_file, encoding="utf-8", delimiter=",")
        df = df[["date", "category", "amount"]]
        df["date"] = pd.to_datetime(df["date"], dayfirst=True)

        current_date = datetime.now()
        filter_date = current_date.replace(day=1)

        df = df[df["date"].dt.normalize() >= pd.Timestamp(filter_date.date())]
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df["amount"] = df["amount"].astype(str).str.replace(r"[^\d.]", "", regex=True)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df = df[df["category"] != "Зарплата"]
        dict_result = df.to_dict(orient="records")
        category_sum = df.groupby("category")["amount"].sum()
        category_sum = category_sum.sort_values(ascending=False)
        total_amount = df["amount"].sum()

        report_lines = []
        for category, amount in category_sum.items():
            report_lines.append(f"{category}: {amount}")

        category_report = "\n".join(report_lines)
        return dict_result, category_report, f"Сумма: {int(total_amount)}"
    except Exception as e:
        print(f"Ошибка обработки CSV файла: {e}")
