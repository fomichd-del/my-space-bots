import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os
from PIL import Image

def get_moon_phase(obs):
    try:
        m = ephem.Moon(obs)
        p = m.phase / 100
        if p < 0.05: return "Новолуние"
        elif p < 0.45: return f"Растущая ({int(p*100)}%)"
        elif p < 0.55: return "1-я четверть"
        elif p < 0.95: return f"Растущая ({int(p*100)}%)"
        else: return "Полнолуние"
    except:
        return "Расчет..."

def draw_line(ax, obs, star1, star2, color='white', lw=1.5):
    try:
        s1, s2 = ephem.star(star1), ephem.star(star2)
        s1.compute(obs); s2.compute(obs)
        if s1.alt > 0 and s2.alt > 0:
            ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=0.8)
    except: pass

def generate_star_map(lat, lon, user_name="Навигатор"):
    try:
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()

        # 1. Загружаем твой идеальный фон
        try:
            bg_img = Image.open('background.png')
        except FileNotFoundError:
            return False, "⚠️ Файл background.png не найден на сервере!"

        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)

        # Кладем фон на холст
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(bg_img)
        ax_bg.axis('off')

        # 2. Накладываем прозрачную карту звездного неба поверх круга
        # Координаты [left, bottom, width, height] подогнаны под твой шаблон
        ax = fig.add_axes([0.165, 0.41, 0.67, 0.42], projection='polar')
        ax.set_facecolor('none') # Карта прозрачная, видно черный круг шаблона
        
        # Настройка ориентации Севера
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.axis('off') # Отключаем системную сетку и рамки

        # --- ЗВЕЗДЫ ---
        np.random.seed(int(float(lat) * 100))
        fx = np.random.uniform(0, 2*np.pi, 2500)
        fy = np.random.uniform(0, np.pi/2, 2500)
        sizes = np.random.uniform(0.5, 2.5, 2500)
        ax.scatter(fx, fy, s=sizes, c='#D4E6FF', alpha=0.7, edgecolors='none')

        # --- СОЗВЕЗДИЯ ---
        c_color = '#FFD700'
        uma = ['Alkaid', 'Mizar', 'Alioth', 'Megrez', 'Phecda', 'Merak', 'Dubhe']
        for i in range(len(uma)-1): draw_line(ax, obs, uma[i], uma[i+1], color=c_color)
        cas = ['Segin', 'Ruchbah', 'Gamma Cassiopeiae', 'Schedar', 'Caph']
        for i in range(len(cas)-1): draw_line(ax, obs, cas[i], cas[i+1], color=c_color)
        
        draw_line(ax, obs, 'Betelgeuse', 'Bellatrix', color='#4DA8DA')
        draw_line(ax, obs, 'Bellatrix', 'Rigel', color='#4DA8DA')
        draw_line(ax, obs, 'Rigel', 'Saiph', color='#4DA8DA')
        draw_line(ax, obs, 'Saiph', 'Betelgeuse', color='#4DA8DA')
        draw_line(ax, obs, 'Alnitak', 'Alnilam', color='white', lw=2)
        draw_line(ax, obs, 'Alnilam', 'Mintaka', color='white', lw=2)

        # Луна
        moon = ephem.Moon()
        moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=400, c='#F4F6F0', alpha=0.9)

        # 3. ВПЕЧАТЫВАЕМ ТЕКСТ В ПАНЕЛИ
        sun = ephem.Sun()
        next_rise = ephem.localtime(obs.next_rising(sun)).strftime('%H:%M')
        next_set = ephem.localtime(obs.next_setting(sun)).strftime('%H:%M')

        t_color = '#A5B4D9' # Голубой неон для текста
        f_size = 18

        # Точные координаты (x, y), где x - ширина, y - высота
        # Если текст немного съедет, мы просто подкорректируем эти цифры
        fig.text(0.38, 0.285, user_name.upper(), color=t_color, fontsize=f_size, fontweight='bold', va='center')
        fig.text(0.50, 0.233, f"{float(lat):.2f}°N, {float(lon):.2f}°E", color=t_color, fontsize=f_size, fontweight='bold', va='center')
        fig.text(0.38, 0.180, get_moon_phase(obs), color=t_color, fontsize=f_size, fontweight='bold', va='center')
        
        fig.text(0.35, 0.128, next_rise, color=t_color, fontsize=f_size, fontweight='bold', va='center')
        fig.text(0.75, 0.128, next_set, color=t_color, fontsize=f_size, fontweight='bold', va='center')
        
        fig.text(0.38, 0.075, "СОЗВЕЗДИЯ И ПЛАНЕТЫ", color=t_color, fontsize=f_size, fontweight='bold', va='center')

        # Сохраняем готовую красоту
        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)

        return True, path
    except Exception as e:
        return False, f"Ошибка отрисовки: {str(e)}"
