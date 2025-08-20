import os
from dotenv import load_dotenv
import telebot
import requests
import uuid

# Загружаем .env
load_dotenv()

# Получаем переменные
BOT_TOKEN = os.getenv("BOT_TOKEN")
GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")

# Проверяем, что все ключи есть
if not all([BOT_TOKEN, GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET]):
    raise ValueError("Ошибка: Не все ключи (.env) заданы!")
print(f"BOT_TOKEN: {BOT_TOKEN[:5]}...")
print(f"GIGACHAT_CLIENT_ID: {GIGACHAT_CLIENT_ID[:5]}...")

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text:
        user_query = message.text
        print(f"Получено сообщение: {user_query}")
        response = get_gigachat_response(user_query)
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Пожалуйста, отправьте текстовый запрос.")

def get_gigachat_response(query):
    # Шаг 1: Получаем токен авторизации
    auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4())
    }
    auth_data = {'scope': 'GIGACHAT_API_PERS'}
    auth = requests.auth.HTTPBasicAuth(GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET)
    
    print("Попытка авторизации...")
    
    try:
        auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data, auth=auth, verify=False)
        print(f"Auth статус: {auth_response.status_code}, Ответ: {auth_response.text}")
        
        if auth_response.status_code != 200:
            return f"Ошибка авторизации: {auth_response.text}"
        
        token = auth_response.json()['access_token']
        print(f"Токен: {token[:10]}...")
    except Exception as e:
        print(f"Ошибка при авторизации: {e}")
        return f"Ошибка: Не удалось подключиться к GigaChat. {e}"
    
    # Шаг 2: Запрос к GigaChat
    chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    chat_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    chat_body = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": "Ты — полезный ассистент."},
            {"role": "user", "content": query}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    print("Отправка вопроса в GigaChat...")
    
    try:
        chat_response = requests.post(chat_url, headers=chat_headers, json=chat_body, verify=False)
        print(f"Chat статус: {chat_response.status_code}, Ответ: {chat_response.text}")
        
        if chat_response.status_code != 200:
            return f"Ошибка GigaChat: {chat_response.text}"
        
        answer = chat_response.json()['choices'][0]['message']['content']
        print(f"Ответ GigaChat: {answer[:50]}...")
        return answer
    except Exception as e:
        print(f"Ошибка при запросе к GigaChat: {e}")
        return f"Ошибка: GigaChat не ответил. {e}"

if __name__ == '__main__':
    print("Бот запущен!")
    bot.polling()