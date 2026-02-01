from datetime import datetime

import pandas as pd


def csv_to_dict(csv_file):
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

        current_date = datetime.now()
        if current_date.day <= 12:
            filter_date = current_date.replace(day=13)
            if filter_date.month == 1:
                filter_date = filter_date.replace(year=filter_date.year - 1, month=12)
            else:
                filter_date = filter_date.replace(month=filter_date.month - 1)
        else:
            filter_date = current_date.replace(day=13)

        df = df[df["date"] >= filter_date]
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df["amount"] = df["amount"].astype(str).str.replace(r"[^\d.]", "", regex=True)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df = df[df["category"] != "Зарплата"]
        dict_result = df.to_dict(orient="records")
        category_sum = df.groupby("category")["amount"].sum()

        category_sum = category_sum.sort_values(ascending=False)
        report_lines = []
        for category, amount in category_sum.items():
            report_lines.append(f"{category}: {amount}")

        category_report = "\n".join(report_lines)
        return dict_result, category_report
    except Exception as e:
        print(f"Ошибка обработки CSV файла: {e}")


# import asyncio
# from app.core.generate import ai_generate
# async def main():
#     dct = csv_to_dict("../../data.csv")
#     print(dct)
#     print(type(dct))
#     # response = await ai_generate(dct)
#     # print(response)
#
#
# asyncio.run(main())
