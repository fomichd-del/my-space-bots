import numpy as np
import ephem
import matplotlib
matplotlib.use('Agg') # Для работы без монитора
import matplotlib.pyplot as plt
from matplotlib import font_manager
from datetime import datetime
import os

def get_moon_phase(obs):
    try:
        m = ephem.Moon(obs)
        p = m.phase / 100
        if p < 0.05: return "Новолуние 🌑"
        elif p < 0.45: return "Растущий серп 🌙"
        elif p < 0.55: return "Первая четверть 🌓"
        elif p < 0.95: return "Растущая Луна 🌔"
        else: return "Полнолуние 🌕"
    except: return "Уточняется 🌗"

def generate_star_map(lat, lon, user_name="Navigator"):
    try:
        # 1. Настройка наблюдателя
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()
        
        # 2. Создаем вертикальный холст 9:16
        fig = plt.figure(figsize=(10, 16), facecolor='#010515')
        
        # Карта (верхняя часть)
        ax = fig.add_axes([0.1, 0.35, 0.8, 0.6], projection='polar')
        ax.set_facecolor('#010515')
        
        # Звездная пыль Млечного Пути
        fx = np.random.uniform(0, 2*np.pi, 6000)
        fy = np.random.uniform(0, np.pi/2, 6000)
        ax.scatter(fx, fy, s=0.1, c='white', alpha=0.15)

        # Рисуем звезды
        for (mag, name, db) in ephem.stars._stars:
            try:
                s = ephem.star(name)
                s.compute(obs)
                if s.alt > 0 and s.mag < 4.2:
                    size = (5 - s.mag) ** 2.3
                    color = 'white' if s.mag > 1.2 else '#FFFACD'
                    ax.scatter(s.az, np.pi/2 - s.alt, s=size, c=color, alpha=0.8, edgecolors='none')
                    
                    if s.mag < 1.3:
                        ax.text(s.az, np.pi/2 - s.alt, s.name, color='white', 
                                fontsize=8, alpha=0.4, family='sans-serif')
            except: continue

        # Стороны света
        for az, label in zip([0, np.pi/2, np.pi, 3*np.pi/2], ['N', 'E', 'S', 'W']):
            ax.text(az, 1.62, label, color='white', fontsize=20, weight='bold', family='sans-serif')

        # 3. Инфо-панель (нижняя часть)
        sun = ephem.Sun()
        next_rise = obs.next_rising(sun)
        next_set = obs.next_setting(sun)
        
        info_text = (
            f"MARTY ASTRO: YOUR SKY\n"
            f"___________________________\n\n"
            f"PILOT: {user_name[:15].upper()}\n"
            f"POS: {float(lat):.2f}N, {float(lon):.2f}E\n"
            f"MOON: {get_moon_phase(obs)}\n"
            f"RISE: {ephem.localtime(next_rise).strftime('%H:%M')}\n"
            f"SET: {ephem.localtime(next_set).strftime('%H:%M')}\n\n"
            f"TARGET: ORION 🎯"
        )
        
        # Используем стандартный шрифт 'monospace' для текста
        fig.text(0.12, 0.12, info_text, color='#FFD700', fontsize=18, 
                 family='monospace', linespacing=1.9, va='bottom')

        # Очистка
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_axis_off()

        # Сохранение
        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', facecolor='#010515', dpi=120)
        plt.close(fig)
        return path
        
    except Exception as e:
        print(f"Ошибка в draw_map: {e}")
        return None
