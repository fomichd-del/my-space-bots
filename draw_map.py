import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ephem
import os

def generate_star_map(lat, lon, user_name="Navigator"):
    try:
        # Настройка наблюдателя
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)

        # Создаем очень простой холст
        fig, ax = plt.subplots(figsize=(6, 6), facecolor='#010515')
        ax.set_facecolor('#010515')

        # Ищем только 50 самых ярких звезд для скорости
        x, y = [], []
        for (mag, name, db) in ephem.stars._stars:
            try:
                s = ephem.star(name)
                s.compute(obs)
                if s.alt > 0 and s.mag < 2.5: 
                    x.append(s.az)
                    y.append(s.alt)
            except: pass

        if x:
            ax.scatter(x, y, c='white', s=10)

        ax.axis('off')
        
        # Сохраняем в один и тот же файл, чтобы не забивать память
        path = "current_sky.png"
        plt.savefig(path, bbox_inches='tight', facecolor='#010515')
        plt.close(fig)

        return True, path
    except Exception as e:
        # ВОТ ЗДЕСЬ МЫ ЛОВИМ ОШИБКУ
        return False, f"Сбой библиотеки: {str(e)}"
