from config import logger
from channels.telegram import TelegramBot  # Импорт бота из src/telegram.py.
import asyncio
from datetime import datetime, timezone, timedelta

def main():
    try:
        logger.info("Скрипт успешно запущен!")
        bot = TelegramBot() # Создаём бота
        bot_data = asyncio.run(bot.collect_messages_since(since_date=datetime.now(timezone.utc) - timedelta(days=7))) # Собираем сообщения за последние N дней с текущей даты — получаем словарь с сообщениями

        # Выводим результат в консоль для проверки
        print(f"Всего собрано: {len(bot_data['messages'])} сообщений")
        logger.info(f"Telegram-бот завершил сбор сообщений. Найдено: {len(bot_data['messages'])}")
    except Exception as e:
        logger.error(f"Ошибка в main: {str(e)}")

if __name__ == '__main__':
    main()