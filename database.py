import psycopg2
import os
from psycopg2 import pool

# Берем ссылку из настроек Render (которую вы обновите в Шаге 2)
DB_URL = os.getenv('DATABASE_URL')

def get_connection():
    """Создает защищенное соединение с облаком Supabase через SSL"""
    try:
        # Обязательно добавляем sslmode='require' для защиты
        conn = psycopg2.connect(DB_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе: {e}")
        return None

def init_db():
    """Создает таблицу пользователей в облаке при первом запуске"""
    conn = get_connection()
    if not conn: return
    
    cursor = conn.cursor()
    # Используем BIGINT для Telegram ID, так как они очень длинные
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            xp INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("📡 База данных Supabase готова к работе!")

def add_xp(user_id, amount, username="Пилот"):
    """Начисляет опыт и сохраняет в облако навсегда"""
    conn = get_connection()
    if not conn: return
    
    cursor = conn.cursor()
    # Специальная команда: вставить или обновить, если уже есть (UPSERT)
    cursor.execute('''
        INSERT INTO users (user_id, username, xp) 
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) 
        DO UPDATE SET xp = users.xp + EXCLUDED.xp, username = EXCLUDED.username
    ''', (user_id, username, amount))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_stats(user_id):
    """Получает текущий опыт пользователя из облака"""
    conn = get_connection()
    if not conn: return 0
    
    cursor = conn.cursor()
    cursor.execute('SELECT xp FROM users WHERE user_id = %s', (user_id,))
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    return res[0] if res else 0

def get_rank_name(xp):
    """Звания для Владика и его команды"""
    if xp < 50: return "Кадет-наблюдатель 🐣"
    if xp < 150: return "Пилот-исследователь 🚀"
    if xp < 300: return "Старший штурман 🧭"
    if xp < 500: return "Командор орбиты 👨‍🚀"
    return "Адмирал Галактики 👑"
