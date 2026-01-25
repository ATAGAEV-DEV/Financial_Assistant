from datetime import datetime

import pandas as pd


def csv_to_dict(csv_file) -> list | None:
    """Преобразует CSV-файл в список словарей с определённой структурой.

    Функция читает CSV-файл, извлекает столбцы 'date', 'category' и 'amount',
    обрабатывает данные: приводит даты к формату YYYY-MM-DD, фильтрует записи,
    оставляя только те, дата которых не раньше 13-го числа текущего месяца,
    очищает и преобразует суммы к числовому типу.
    """
    try:
        df = pd.read_csv(csv_file, encoding="utf-8", delimiter=",")
        df = df[["date", "category", "amount"]]
        df["date"] = pd.to_datetime(df["date"], dayfirst=True)
        df = df[df["date"] >= datetime(datetime.now().year, datetime.now().month, 13)]
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df["amount"] = df["amount"].astype(str).str.replace(r"[^\d.]", "", regex=True)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        dict_result = df.to_dict(orient="records")
        return dict_result
    except Exception as e:
        print(f"Ошибка обработки CSV файла: {e}")
