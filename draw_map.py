import matplotlib.pyplot as plt
from skyfield.api import Star, load, wgs84
from skyfield.projections import build_stereographic_projection
import numpy as np
from datetime import datetime
import json
import random

def generate_star_map(lat, lon, user_name):
    try:
        # 1. Загрузка данных созвездий
        with open('constellations.json', 'r', encoding='utf-8') as f:
            const_data = json.load(f)
        
        # Выбираем случайную цель (включая зодиакальные)
        target_id = random.choice(list(const_data.keys()))
        target = const_data[target_id]
        
        # 2. Астрономические вычисления
        ts = load.timescale()
        t = ts.now()
        eph = load('de421.bsp')
        earth = eph['earth']
        location = earth + wgs84.latlon(lat, lon)
        
        # Создаем проекцию неба
        observer = location.at(t)
        center = observer.from_altaz(alt_degrees=90, az_degrees=0)
        projection = build_stereographic_projection(center)
        
        # Загружаем звезды (каталог Hipparcos)
        with load.open('hip_main.dat') as f:
            stars = load.hip(f)

        # 3. Рисование
        fig, ax = plt.subplots(figsize=(10, 10), facecolor='#0B0D14')
        ax.set_facecolor('#0B0D14')
        
        # Проецируем звезды
        star_positions = observer.observe(stars)
        x, y = projection(star_positions)
        
        # Рисуем звезды (размер зависит от яркости)
        m = stars.magnitude
        ax.scatter(x, y, s=(12 - m)**2, c='white', alpha=0.8, edgecolors='none')
        
        # ПОДСВЕТКА ЦЕЛИ (Красный неон)
        # Ищем звезду-якорь для созвездия
        anchor_star = stars[target['anchor_hip']]
        tx, ty = projection(observer.observe(anchor_star))
        
        ax.scatter(tx, ty, s=400, facecolors='none', edgecolors='#FF0033', linewidth=2, alpha=0.6)
        ax.text(tx, ty + 0.02, "[ ЦЕЛЬ ]", color='#FF0033', fontsize=10, fontweight='bold', ha='center')

        # Оформление
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.axis('off')
        
        plt.title(f"СЕКТОР: {user_name.upper()} | {datetime.now().strftime('%d.%m.%Y %H:%M')}", 
                  color='#4A90E2', fontsize=12, pad=-20)

        # Сохранение
        filename = f"map_{random.randint(1000, 9999)}.png"
        plt.savefig(filename, bbox_inches='tight', pad_inches=0.2, dpi=150)
        plt.close()

        return True, filename, target['name'], target['fact']

    except Exception as e:
        return False, str(e), None, None
