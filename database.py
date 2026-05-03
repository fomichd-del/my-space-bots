import psycopg2
import os

# Ссылка из настроек Render
DB_URL = os.getenv('DATABASE_URL')

def get_connection():
    """Создает соединение с облаком Supabase"""
    return psycopg2.connect(DB_URL)

def init_db():
    """Создает таблицу пользователей в облаке"""
    conn = get_connection()
    cursor = conn.cursor()
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

def add_xp(user_id, amount, username="Пилот"):
    """Начисляет опыт и сохраняет навсегда"""
    conn = get_connection()
    cursor = conn.cursor()
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
    """Получает текущий XP из облака"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT xp FROM users WHERE user_id = %s', (user_id,))
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    return res[0] if res else 0

def get_rank_name(xp):
    """Звания для Владика и команды"""
    if xp < 50: return "Кадет-наблюдатель 🐣"
    if xp < 150: return "Пилот-исследователь 🚀"
    if xp < 300: return "Старший штурман 🧭"
    if xp < 500: return "Командор орбиты 👨‍🚀"
    return "Адмирал Галактики 👑"
