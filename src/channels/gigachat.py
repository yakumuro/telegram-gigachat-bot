import requests
import uuid
import json
import re
from config import logger, GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET


def analyze_chat(messages_data):
    messages = messages_data.get("messages", [])
    if not messages:
        return {
            "analysis_period": {"from": "", "to": ""},
            "total_messages_processed": 0,
            "filtered_out": 0,
            "used_in_analysis": 0,
            "feature_requests": [],
            "bugs": [],
            "filtered_messages_examples": ["Нет сообщений для анализа"]
        }

    # Формируем системный промт
    system_prompt = f'''Ты — аналитик продукта в компании, разрабатывающей систему "Базон".
Тебе предоставлен список сообщений из Telegram-группы, собранных за определённый период.
Твоя задача — проанализировать сообщения и вернуть результат в строгом формате JSON.

Задача:
Проанализируй все сообщения и выполни:

1. Определи период анализа.
2. Отфильтруй ненужные сообщения:
   - Спам, флуд (эмодзи, "ахах", "привет"),
   - Личные темы (зарплата, встречи, быт),
   - Оскорбления, троллинг.
3. Раздели оставшиеся на категории:
   - feature_requests — пожелания по улучшению
   - bugs — сообщения о багах
4. Сгруппируй похожие сообщения:
   - Объедини одинаковые/схожие по смыслу.
   - Для каждой группы укажи:
     - summary — краткая суть
     - examples — 2–3 оригинальных формулировки
     - count — количество упоминаний

Формат вывода (обязательно!):
{{
  "analysis_period": {{
    "from": "YYYY-MM-DDTHH:MM:SS+00:00",
    "to": "YYYY-MM-DDTHH:MM:SS+00:00"
  }},
  "total_messages_processed": # (укажи сколько всего сообщений получилось проанализировать)
  "filtered_out": # (укажи, сколько сообщений оказались флудом спамом и так далее)
  "used_in_analysis": # (укажи сколько целевых сообщений)
  "feature_requests": [ # Здесь отобрази сгруппированные пожелания
    {{
      "summary": "Добавить экспорт в Excel",
      "count": 12,
      "examples": [
        "Сделайте экспорт в Excel, пожалуйста",
        "Нужно выгружать отчёты в XLSX",
        "Экспорт в Excel — must have"
      ]
    }}
  ],
  "bugs": [ # Здесь отобрази сгруппированные баги
    {{
      "summary": "Ошибка при сохранении формы",
      "count": 5,
      "examples": [
        "При нажатии 'Сохранить' — ошибка 500",
        "Форма не сохраняется, белый экран"
      ]
    }}
  ],
  "filtered_messages_examples": [ # Здесь отобрази примеры флуд и спам сообщений
    "ахаха",
    "кто тут?",
    "продам аккаунт"
  ]
}}

Правила:
- Возвращай ответ в формате JSON
- Не добавляй поля, которых нет в образце.
- Если категория пустая — оставь пустой массив [].
- Все даты — в ISO 8601 (UTC).
- Не выдумывай данные. Только на основе входных сообщений.
- Не объединяй несвязанные темы.
- Не используй markdown, кавычки, ```json и т.п. Только чистый JSON.
'''

    # Шаг 1: Получение токена
    auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4())
    }
    auth_data = {'scope': 'GIGACHAT_API_PERS'}
    auth = requests.auth.HTTPBasicAuth(GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET)

    logger.info("Запрос токена авторизации у GigaChat...")

    try:
        auth_response = requests.post(
            auth_url,
            headers=auth_headers,
            data=auth_data,
            auth=auth,
            verify=False
        )
        if auth_response.status_code != 200:
            logger.error(f"Ошибка авторизации: {auth_response.status_code}, {auth_response.text}")
            return {"error": "Не удалось получить токен"}
        token = auth_response.json()['access_token']
        logger.info("Токен GigaChat получен.")
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {e}")
        return {"error": f"Сеть: {e}"}

    # Шаг 2: Запрос к GigaChat
    chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    chat_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    chat_body = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(messages, ensure_ascii=False, indent=2)}
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
        "top_p": 0.1,
        "stream": False
    }

    logger.info("Отправка запроса в GigaChat...")
    try:
        response = requests.post(
            chat_url,
            headers=chat_headers,
            json=chat_body,
            verify=False
        )
        if response.status_code != 200:
            logger.error(f"Ошибка GigaChat: {response.status_code}, {response.text}")
            return {"error": f"API ошибка: {response.text}"}

        raw_text = response.json()['choices'][0]['message']['content'].strip()
        logger.debug(f"Сырой ответ GigaChat: {raw_text[:500]}...")

        # Пытаемся извлечь JSON
        try:
            # Удаляем возможные обёртки
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                cleaned = json_match.group(0)
                result = json.loads(cleaned)
                logger.info("JSON успешно распарсен.")
                return result
            else:
                logger.error("Не удалось найти JSON в ответе.")
                return {"error": "GigaChat не вернул валидный JSON", "raw_response": raw_text}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return {"error": "Некорректный JSON", "raw_response": raw_text}

    except Exception as e:
        logger.error(f"Ошибка при запросе к GigaChat: {e}")
        return {"error": f"Ошибка сети: {str(e)}"}