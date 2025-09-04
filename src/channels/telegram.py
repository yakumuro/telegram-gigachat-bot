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