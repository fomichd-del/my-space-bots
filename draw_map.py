import numpy as np
import ephem
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import os

def generate_star_map(lat, lon, user_name="Navigator"):
    try:
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()
        
        # Создаем холст
        fig = plt.figure(figsize=(8, 12), facecolor='#010515')
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection='polar')
        ax.set_facecolor('#010515')
        
        # Находим звезды
        stars_x = []
        stars_y = []
        for (mag, name, db) in ephem.stars._stars:
            try:
                s = ephem.star(name)
                s.compute(obs)
                if s.alt > 0 and s.mag < 4.0:
                    stars_x.append(s.az)
                    stars_y.append(np.pi/2 - s.alt)
            except: continue
        
        # Рисуем все звезды одним махом (так быстрее и надежнее)
        if stars_x:
            ax.scatter(stars_x, stars_y, s=10, c='white', alpha=0.8)

        # Убираем всё лишнее
        ax.set_axis_off()
        
        # Добавляем подпись внизу
        plt.figtext(0.5, 0.05, f"SKY FOR {user_name.upper()}\n{lat:.2f}, {lon:.2f}", 
                    color='gold', ha='center', fontsize=12)

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', facecolor='#010515')
        plt.close(fig)
        return path
    except Exception as e:
        print(f"ERROR: {e}")
        return None
