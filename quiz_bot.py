import requests
import os
import random

# Данные для доступа (берутся из секретов GitHub)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

# Наша база знаний (пока 3 вопроса, добавим еще 27!)
quiz_data = [
    {
        "question": "Как на МКС справляются с грязной одеждой? 🧼",
        "options": ["Стирают в мини-машинке", "Выветривают в космосе", "Просто выбрасывают"],
        "correct_id": 2,
        "explanation": "Вода на МКС слишком дорога, поэтому одежду носят долго, а потом утилизируют! 🚮"
    },
    {
        "question": "Зачем под ракету при старте льют тысячи тонн воды? 🌊",
        "options": ["Чтобы помыть площадку", "Чтобы погасить звук", "Чтобы охладить воздух"],
        "correct_id": 1,
        "explanation": "Звуковая волна от двигателей так сильна, что может разрушить ракету. Вода гасит этот шум! 🔊"
    },
    {
        "question": "На какой планете идут дожди из настоящих алмазов? 💎",
        "options": ["Венера", "Марс", "Сатурн"],
        "correct_id": 2,
        "explanation": "Давление в атмосфере Сатурна и Юпитера так велико, что углерод превращается в алмазы! 🪐"
    }
]

def send_quiz():
    # Выбираем случайный вопрос из списка
    item = random.choice(quiz_data)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPoll"
    
    payload = {
        "chat_id": CHANNEL_NAME,
        "question": item["question"],
        "options": item["options"],
        "is_anonymous": False,
        "type": "quiz",
        "correct_option_id": item["correct_id"],
        "explanation": item["explanation"],
        "explanation_parse_mode": "HTML"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Ошибка при отправке: {response.text}")

if __name__ == '__main__':
    send_quiz()
