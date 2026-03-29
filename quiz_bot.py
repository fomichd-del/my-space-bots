import requests
import os
import random

# Настройки доступа
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

# Наша база знаний (пока добавим один вопрос для теста)
quiz_data = [
    {
        "question": "Как космонавты на МКС справляются с грязной одеждой? 🧼",
        "options": [
            "Используют мини-машинку", 
            "Выветривают в космосе", 
            "Выбрасывают грязное белье"
        ],
        "correct_id": 2,
        "explanation": "Вода на станции слишком дорога, поэтому одежду просто утилизируют в грузовике! 🚮"
    }
    # Сюда мы добавим остальные 29 вопросов позже
]

def send_quiz():
    # Выбираем случайный вопрос
    item = random.choice(quiz_data)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPoll"
    
    payload = {
        "chat_id": CHANNEL_NAME,
        "question": item["question"],
        "options": item["options"],
        "is_anonymous": False,      # Чтобы видеть, как голосуют (по желанию)
        "type": "quiz",             # Режим викторины
        "correct_option_id": item["correct_id"],
        "explanation": item["explanation"],
        "explanation_parse_mode": "HTML"
    }
    
    requests.post(url, json=payload)

if __name__ == '__main__':
    send_quiz()
