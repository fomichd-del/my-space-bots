import psycopg2
import os
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
DB_URL = os.getenv('DATABASE_URL')

def get_connection():
    try:
        return psycopg2.connect(DB_URL, sslmode='require')
    except Exception as e:
        print(f"❌ Ошибка связи с базой: {e}")
        return None

def init_db():
    """Инициализация таблиц и добавление новых колонок геймификации"""
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        # Создание основной таблицы, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                xp INTEGER DEFAULT 0,
                personal_log TEXT DEFAULT ''
            )
        ''')
        
        # Список новых колонок для системы Академии Орион 2.0
        new_columns = [
            ("spendable_dust", "INTEGER DEFAULT 0"),   # Кошелек (валюта)
            ("jackpot_claimed", "BOOLEAN DEFAULT FALSE"), # Флаг джекпота
            ("streak_days", "INTEGER DEFAULT 0"),      # Серия дней (стрик)
            ("last_active_date", "TEXT DEFAULT ''")    # Дата последней активности
        ]
        
        # Безопасное добавление колонок через проверку существования
        for col_name, col_type in new_columns:
            cursor.execute(f'''
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='users' AND column_name='{col_name}') THEN 
                        ALTER TABLE users ADD COLUMN {col_name} {col_type};
                    END IF; 
                END $$;
            ''')
        
        conn.commit()
        print("📡 [СИСТЕМА] База данных Академии Орион полностью синхронизирована.")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
    finally:
        cursor.close()
        conn.close()

def add_xp(user_id, amount, username="Пилот"):
    """Начисляет опыт (ранг) и звездную пыль (кошелек) одновременно"""
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, username, xp, spendable_dust) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                xp = users.xp + EXCLUDED.xp, 
                spendable_dust = users.spendable_dust + EXCLUDED.spendable_dust,
                username = EXCLUDED.username
        ''', (user_id, username, amount, amount))
        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка начисления XP: {e}")
    finally:
        cursor.close()
        conn.close()

def get_user_stats(user_id):
    """Возвращает текущий XP пользователя"""
    conn = get_connection()
    if not conn: return 0
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT xp FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        return res[0] if res else 0
    finally:
        cursor.close()
        conn.close()

def get_user_data(user_id):
    """Получает полный пакет данных пилота для логики бота"""
    conn = get_connection()
    if not conn: return {"xp": 0, "spendable_dust": 0, "jackpot_claimed": False, "streak_days": 0}
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT xp, spendable_dust, jackpot_claimed, streak_days FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        if res:
            return {
                "xp": res[0], 
                "spendable_dust": res[1], 
                "jackpot_claimed": res[2], 
                "streak_days": res[3]
            }
        return {"xp": 0, "spendable_dust": 0, "jackpot_claimed": False, "streak_days": 0}
    finally:
        cursor.close()
        conn.close()

def set_jackpot_claimed(user_id):
    """Блокирует повторное получение джекпота"""
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET jackpot_claimed = TRUE WHERE user_id = %s', (user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def spend_dust(user_id, amount):
    """Списывает пыль только из кошелька (ранг не меняется)"""
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET spendable_dust = spendable_dust - %s 
            WHERE user_id = %s AND spendable_dust >= %s
        ''', (amount, user_id, amount))
        if cursor.rowcount > 0:
            conn.commit()
            return True
        return False
    finally:
        cursor.close()
        conn.close()

def check_and_update_streak(user_id):
    """Обрабатывает серию ежедневных посещений"""
    conn = get_connection()
    if not conn: return 0
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        cursor = conn.cursor()
        cursor.execute('SELECT last_active_date, streak_days FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        
        if not res: return 0
            
        last_date, streak = res
        if last_date == current_date: return streak
            
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        new_streak = streak + 1 if last_date == yesterday else 1
            
        cursor.execute('UPDATE users SET last_active_date = %s, streak_days = %s WHERE user_id = %s', 
                       (current_date, new_streak, user_id))
        conn.commit()
        return new_streak
    finally:
        cursor.close()
        conn.close()

def get_top_pilots(limit=5):
    """Данные для команды Радар"""
    conn = get_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT username, xp FROM users ORDER BY xp DESC LIMIT %s', (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def update_personal_log(user_id, new_info):
    """Запись воспоминаний в память Марти"""
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET personal_log = CASE 
                WHEN personal_log IS NULL OR personal_log = '' THEN %s 
                ELSE personal_log || ' | ' || %s 
            END
            WHERE user_id = %s
        ''', (new_info, new_info, user_id))
        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка обновления лога: {e}")
    finally:
        cursor.close()
        conn.close()

def get_personal_log(user_id):
    conn = get_connection()
    if not conn: return ""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT personal_log FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        return res[0] if res and res[0] else "Данных пока нет. Начните исследование!"
    finally:
        cursor.close()
        conn.close()

# 🏆 ХАРДКОРНАЯ ШКАЛА РАНГОВ АКАДЕМИИ ОРИОН
def get_rank_name(xp):
    if xp < 15: return "Космический Кадет 🚀"
    if xp < 40: return "Навигатор Орбиты 🛰"
    if xp < 80: return "Бортинженер 🔧"
    if xp < 130: return "Астро-Исследователь 🔭"
    if xp < 200: return "Учёный Пилот 🪐"
    if xp < 300: return "Капитан Корабля 🛸"
    if xp < 450: return "Командор Галактики 🎖"
    if xp < 650: return "Адмирал Флота ⭐"
    if xp < 900: return "Академик Космоса 🎓"
    return "Верный Помощник Марти 🐕"
