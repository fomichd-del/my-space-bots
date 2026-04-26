import numpy as np
import ephem
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import os

def generate_star_map(lat, lon, user_name="Navigator"):
    try:
        # Установка наблюдателя
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()
        
        # Создаем холст 9:16
        fig, ax = plt.subplots(figsize=(10, 16), facecolor='#010515')
        ax.set_facecolor('#010515')
        
        # Рисуем "звездную пыль" (фон)
        for _ in range(300):
            ax.plot(np.random.rand(), np.random.rand(), 'wo', ms=0.5, alpha=0.3)

        # Рисуем основные звезды
        stars_found = 0
        for (mag, name, db) in ephem.stars._stars:
            try:
                s = ephem.star(name)
                s.compute(obs)
                if s.alt > 0 and s.mag < 4.5:
                    # Переводим азимут и высоту в простые координаты X, Y
                    x = (s.az / (2 * np.pi))
                    y = (s.alt / (np.pi / 2))
                    size = (5 - s.mag) * 2
                    ax.plot(x, y, 'wo', ms=size, alpha=0.8)
                    stars_found += 1
            except: continue

        # Если звезд не нашли, рисуем хоть что-то, чтобы не было ошибки
        if stars_found == 0:
            ax.text(0.5, 0.5, "Слишком облачно...", color='white', ha='center')

        # Заголовок и инфо
        info = (
            f"MARTY ASTRO: YOUR SKY\n"
            f"----------------------\n"
            f"PILOT: {user_name.upper()}\n"
            f"POS: {float(lat):.2f}, {float(lon):.2f}\n"
            f"TARGET: ORION 🎯"
        )
        plt.figtext(0.15, 0.15, info, color='#FFD700', fontsize=18, family='monospace')

        # Убираем оси
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.2)
        ax.axis('off')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', facecolor='#010515', dpi=100)
        plt.close(fig)
        return path

    except Exception as e:
        print(f"ОШИБКА В РИСОВАНИИ: {e}")
        return None
