import os
from datetime import datetime

from dotenv import load_dotenv
from openai import APIConnectionError, APIError, AsyncOpenAI, BadRequestError
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.tools.prompt import SYSTEM_PROMPT
from app.tools.utils import clean_text

load_dotenv()

AI_TOKEN_POLZA = os.getenv("AI_TOKEN_POLZA")
polza = "https://api.polza.ai/api/v1"

client = AsyncOpenAI(
    api_key=AI_TOKEN_POLZA,
    base_url=polza,
)


async def ai_generate(expenses: list) -> str | None:
    """Асинхронно генерирует текстовый анализ списка трат с использованием модели ИИ.

    Функция формирует промпт на основе переданных трат, отправляет его в модель ИИ
    через API и возвращает отформатированный ответ. В случае ошибок выводит сообщение
    в консоль и возвращает None.
    """
    message = generate_prompt(expenses)
    try:
        completion = await client.chat.completions.create(
            model="google/gemini-3-flash-preview", messages=message, temperature=0.3, max_tokens=5000
        )

        response_text = completion.choices[0].message.content
        response = clean_text(response_text)
        return response

    except BadRequestError as e:
        print(f"Ошибка запроса к API: {e}")

    except APIConnectionError as e:
        print(f"Ошибка подключения к API: {e}")

    except APIError as e:
        print(f"Ошибка API: {e}")

    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


def generate_prompt(expenses: list) -> list:
    """Формирует системный и пользовательский промпты для отправки в модель ИИ.

    Создаёт список сообщений, включающий системное сообщение с промптом и датой,
    а также пользовательское сообщение со списком трат.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    message = [
        ChatCompletionSystemMessageParam(
            role="system", content=SYSTEM_PROMPT + f"Дата на сегодня: {today}"
        ),
        ChatCompletionUserMessageParam(role="user", content=str(expenses)),
    ]

    return message
