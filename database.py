import psycopg2
import os

DB_URL = os.getenv('DATABASE_URL')

def get_connection():
    """Создает защищенное соединение с облаком Supabase"""
    try:
        return psycopg2.connect(DB_URL, sslmode='require')
    except Exception as e:
        print(f"❌ Ошибка подключения к базе: {e}")
        return None

def init_db():
    """Создает таблицу пользователей с поддержкой долгосрочной памяти"""
    conn = get_connection()
    if not conn: return
    
    try:
        cursor = conn.cursor()
        # Добавляем колонку personal_log для хранения памяти о пользователе
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                xp INTEGER DEFAULT 0,
                personal_log TEXT DEFAULT ''
            )
        ''')
        conn.commit()
        print("📡 [СИСТЕМА] База данных Supabase готова (память активна).")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
    finally:
        cursor.close()
        conn.close()

def update_personal_log(user_id, new_info):
    """Добавляет новые факты в бортовой журнал пилота"""
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        # Склеиваем старую память с новой записью через разделитель
        cursor.execute('''
            UPDATE users 
            SET personal_log = personal_log || ' | ' || %s 
            WHERE user_id = %s
        ''', (new_info, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_personal_log(user_id):
    """Получает всё, что Марти помнит о пилоте"""
    conn = get_connection()
    if not conn: return ""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT personal_log FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        return res[0] if res and res[0] else "Данных пока нет."
    finally:
        cursor.close()
        conn.close()

# Оставляем остальные функции (add_xp, get_user_stats) без изменений...
