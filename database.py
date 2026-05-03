import psycopg2
import os

# Ссылка берется из настроек Render (Environment Variables)
# Убедитесь, что в Render переменная DATABASE_URL совпадает с вашей новой строкой
DB_URL = os.getenv('DATABASE_URL')

def get_connection():
    """Создает защищенное соединение с облаком Supabase"""
    try:
        # Добавляем sslmode='require', это обязательное требование Supabase
        return psycopg2.connect(DB_URL, sslmode='require')
    except Exception as e:
        print(f"❌ Ошибка подключения к базе: {e}")
        return None

def init_db():
    """Создает таблицу пользователей в облаке при старте"""
    conn = get_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        # Используем BIGINT для Telegram ID (они бывают очень длинными)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                xp INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        print("📡 [СИСТЕМА] База данных Supabase успешно инициализирована.")
    except Exception as e:
        print(f"❌ Ошибка инициализации таблицы: {e}")
    finally:
        cursor.close()
        conn.close()

def add_xp(user_id, amount, username="Пилот"):
    """Начисляет опыт и сохраняет в облако (UPSERT)"""
    conn = get_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        # Вставляем нового или обновляем существующего (команда ON CONFLICT)
        cursor.execute('''
            INSERT INTO users (user_id, username, xp) 
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET xp = users.xp + EXCLUDED.xp, username = EXCLUDED.username
        ''', (user_id, username, amount))
        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка при начислении XP: {e}")
    finally:
        cursor.close()
        conn.close()

def get_user_stats(user_id):
    """Получает текущий XP пользователя из облака"""
    conn = get_connection()
    if not conn:
        return 0
    
    xp = 0
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT xp FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        if res:
            xp = res[0]
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
    finally:
        cursor.close()
        conn.close()
    return xp

def get_rank_name(xp):
    """Система космических званий"""
    if xp < 50: return "Кадет-наблюдатель 🐣"
    if xp < 150: return "Пилот-исследователь 🚀"
    if xp < 300: return "Старший штурман 🧭"
    if xp < 500: return "Командор орбиты 👨‍🚀"
    return "Адмирал Галактики 👑"
