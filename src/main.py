from config import logger
from channels.telegram import TelegramBot
from channels.gigachat import analyze_chat
import asyncio
from datetime import datetime, timezone, timedelta
import json
import os

def save_result(data, filename="output/analysis_result.json"):

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"✅ Результат анализа сохранён в {filename}")
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении файла: {e}")

def main():
    try:
        logger.info("Скрипт успешно запущен!")

        # 1. Собираем сообщения из группы
        bot = TelegramBot()
        bot_data = asyncio.run(bot.collect_messages_since(since_date=datetime.now(timezone.utc) - timedelta(days=3)))
        print(f"Всего собрано: {len(bot_data['messages'])} сообщений")
        logger.info(f"Telegram-бот завершил сбор сообщений. Найдено: {len(bot_data['messages'])}")

        # 2. Анализ через GigaChat
        analysis_result = analyze_chat(bot_data)

        # 3. Сохранение
        save_result(analysis_result)

        # 4. Вывод в консоль
        print(f"Анализ завершён. Результат сохранён в output/analysis_result.json")
        if "error" in analysis_result:
            print(f"Ошибка: {analysis_result['error']}")


    except Exception as e:
        logger.error(f"Ошибка в main: {str(e)}")

if __name__ == '__main__':
    main()

def save_result(data, filename="output/analysis_result.json"):
    """Сохраняет результат в JSON"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Результат сохранён в {filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении: {e}")