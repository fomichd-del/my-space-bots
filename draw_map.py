import numpy as np
import ephem
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import os

def generate_star_map(lat, lon, user_name="Navigator"):
    try:
        print("Начинаю отрисовку карты (безопасный режим)...")
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()
        
        # Создаем холст
        fig = plt.figure(figsize=(8, 12), facecolor='#010515')
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection='polar')
        ax.set_facecolor('#010515')
        
        # Собираем и рисуем звезды (БЕЗ ТЕКСТА)
        stars_x = []
        stars_y = []
        sizes = []
        for (mag, name, db) in ephem.stars._stars:
            try:
                s = ephem.star(name)
                s.compute(obs)
                if s.alt > 0 and s.mag < 4.0:
                    stars_x.append(s.az)
                    stars_y.append(np.pi/2 - s.alt)
                    sizes.append((5-s.mag)**2) # Размер зависит от яркости
            except: continue
        
        if stars_x:
            ax.scatter(stars_x, stars_y, s=sizes, c='white', alpha=0.8)

        # Выключаем оси и рамки
        ax.set_axis_off()

        # Сохраняем картинку
        path = f"sky_safe_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', facecolor='#010515')
        plt.close(fig)
        
        print(f"Карта успешно сохранена: {path}")
        return path
        
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА РИСОВАНИЯ: {e}")
        return None
