from config import logger, API_ID, API_HASH, PHONE, GROUP_ID
from telethon import TelegramClient
import asyncio
from datetime import datetime, timezone

bot = None

async def auth(): # Создаёт и возвращает экземпляр TelegramBot. Вызывается один раз при старте.
    global bot
    if bot is None:
        bot = TelegramBot()
    return bot


class TelegramBot:
    def __init__(self):
        self.api_id = API_ID
        self.api_hash = API_HASH
        self.phone = PHONE
        self.group_id = int(GROUP_ID)
        self.messages = {"messages": []}
        self.seen_message_ids = set()
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        logger.info('Клиент Telethon инициализирован.')

    async def collect_messages_since(self, since_date=None):
        try:
            await self.client.start(phone=self.phone)
            logger.info('Авторизация прошла успешно.')
            await self.client.get_dialogs()
            logger.info('Диалоги загружены.')

            self.messages = {"messages": []}
            self.seen_message_ids.clear()

            logger.info(f'Сбор сообщений из группы {self.group_id}...')
            if since_date:
                logger.info(f"Фильтр: сообщения с {since_date.isoformat()}")
            else:
                logger.info("Фильтр: все доступные сообщения")

            count = 0
            # Ограничиваем количество загружаемых сообщений
            async for message in self.client.iter_messages(self.group_id, limit=None):
                # Прекращаем, если сообщение слишком старое
                if since_date and message.date < since_date:
                    logger.debug("Достигнута граница по дате — остановка сбора.")
                    break  # Выходим из цикла т.к дальше только старые сообщения

                if not message.text or message.id in self.seen_message_ids:
                    continue

                try:
                    sender = await message.get_sender()
                except Exception as e:
                    logger.debug(f"Не удалось получить отправителя для {message.id}: {e}")
                    sender = None

                if sender is None:
                    user_id = "unknown"
                    username = "Аноним"
                else:
                    user_id = getattr(sender, 'id', 'unknown')
                    first_name = getattr(sender, 'first_name', '')
                    last_name = getattr(sender, 'last_name', '')
                    username = first_name
                    if last_name:
                        username += f" {last_name}"
                    username = username.strip() or getattr(sender, 'username', 'Аноним')
                    if username != 'Аноним' and not username.startswith('@'):
                        username = f"@{username}" if getattr(sender, 'username') else username

                self.messages["messages"].append({
                    "author_id": user_id,
                    "author_name": username,
                    "date": message.date.isoformat(),
                    "text": message.text
                })
                self.seen_message_ids.add(message.id)
                count += 1

            logger.info(f'Сбор завершён. Добавлено {count} сообщений.')
            return self.messages

        except Exception as e:
            logger.error(f'Ошибка при сборе сообщений: {e}')
            return {"messages": []}
        finally:
            if self.client.is_connected():
                await self.client.disconnect()
                logger.info("Клиент отключён.")


# # Проверяем, что все ключи есть
# if not all([BOT_TOKEN, GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET]):
#     raise ValueError("Ошибка: Не все ключи (.env) заданы!")
# print(f"BOT_TOKEN: {BOT_TOKEN[:5]}...")
# print(f"GIGACHAT_CLIENT_ID: {GIGACHAT_CLIENT_ID[:5]}...")

# # Инициализация бота
# bot = telebot.TeleBot(BOT_TOKEN)

# @bot.message_handler(func=lambda message: True)
# def handle_message(message):
#     if message.text:
#         user_query = message.text
#         print(f"Получено сообщение: {user_query}")
#         response = get_gigachat_response(user_query)
#         bot.reply_to(message, response)
#     else:
#         bot.reply_to(message, "Пожалуйста, отправьте текстовый запрос.")

# def get_gigachat_response(query):
#     # Шаг 1: Получаем токен авторизации
#     auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
#     auth_headers = {
#         'Content-Type': 'application/x-www-form-urlencoded',
#         'Accept': 'application/json',
#         'RqUID': str(uuid.uuid4())
#     }
#     auth_data = {'scope': 'GIGACHAT_API_PERS'}
#     auth = requests.auth.HTTPBasicAuth(GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET)
    
#     print("Попытка авторизации...")
    
#     try:
#         auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data, auth=auth, verify=False)
#         print(f"Auth статус: {auth_response.status_code}, Ответ: {auth_response.text}")
        
#         if auth_response.status_code != 200:
#             return f"Ошибка авторизации: {auth_response.text}"
        
#         token = auth_response.json()['access_token']
#         print(f"Токен: {token[:10]}...")
#     except Exception as e:
#         print(f"Ошибка при авторизации: {e}")
#         return f"Ошибка: Не удалось подключиться к GigaChat. {e}"
    
#     # Шаг 2: Запрос к GigaChat
#     chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
#     chat_headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {token}'
#     }
#     chat_body = {
#         "model": "GigaChat",
#         "messages": [
#             {"role": "system", "content": "Ты — полезный ассистент."},
#             {"role": "user", "content": query}
#         ],
#         "temperature": 0.7,
#         "max_tokens": 500
#     }
    
#     print("Отправка вопроса в GigaChat...")
    
#     try:
#         chat_response = requests.post(chat_url, headers=chat_headers, json=chat_body, verify=False)
#         print(f"Chat статус: {chat_response.status_code}, Ответ: {chat_response.text}")
        
#         if chat_response.status_code != 200:
#             return f"Ошибка GigaChat: {chat_response.text}"
        
#         answer = chat_response.json()['choices'][0]['message']['content']
#         print(f"Ответ GigaChat: {answer[:50]}...")
#         return answer
#     except Exception as e:
#         print(f"Ошибка при запросе к GigaChat: {e}")
#         return f"Ошибка: GigaChat не ответил. {e}"

# if __name__ == '__main__':
#     print("Бот запущен!")
#     bot.polling()