import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os
import json
import random
from PIL import Image

# Звезды-Якоря для наведения прицела на созвездия из твоего файла
ANCHOR_STARS = {
    "andromeda": "Alpheratz", "aquarius": "Sadalmelik", "aquila": "Altair",
    "aries": "Hamal", "auriga": "Capella", "bootes": "Arcturus",
    "canes_venatici": "Cor Caroli", "canis_major": "Sirius", "canis_minor": "Procyon",
    "capricornus": "Deneb Algedi", "carina": "Canopus", "cassiopeia": "Schedar",
    "centaurus": "Rigil Kentaurus", "cepheus": "Alderamin", "cetus": "Menkar",
    "columba": "Phact", "corona_borealis": "Alphecca", "corvus": "Alchiba",
    "crater": "Alkes", "crux": "Acrux", "cygnus": "Deneb", "delphinus": "Sualocin",
    "draco": "Thuban", "eridanus": "Achernar", "gemini": "Pollux", "grus": "Alnair",
    "hercules": "Rasalgethi", "hydra": "Alphard", "leo": "Regulus", "lepus": "Arneb",
    "libra": "Zubenelgenubi", "lyra": "Vega", "ophiuchus": "Rasalhague",
    "orion": "Betelgeuse", "pavo": "Peacock", "pegasus": "Markab", "perseus": "Mirfak",
    "phoenix": "Ankaa", "pisces": "Alrescha", "piscis_austrinus": "Fomalhaut",
    "puppis": "Naos", "sagittarius": "Nunki", "scorpius": "Antares", "serpens": "Unukalhai",
    "taurus": "Aldebaran", "triangulum_australe": "Atria", "ursa_major": "Dubhe",
    "ursa_minor": "Polaris", "vela": "Suhail", "virgo": "Spica"
}

def get_moon_phase(obs):
    try:
        m = ephem.Moon(obs)
        p = m.phase / 100
        if p < 0.05: return "Новолуние"
        elif p < 0.45: return f"Растущая ({int(p*100)}%)"
        elif p < 0.55: return "Первая четверть"
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

        # 1. ЗАГРУЖАЕМ ТВОЮ БАЗУ ДАННЫХ
        try:
            with open('constellations.json', 'r', encoding='utf-8') as f:
                constellations_db = json.load(f)
        except Exception as e:
            print("Ошибка загрузки constellations.json:", e)
            constellations_db = {}

        # 2. ИЩЕМ ВИДИМЫЕ ЦЕЛИ
        visible_targets = []
        for key, anchor in ANCHOR_STARS.items():
            if key in constellations_db:
                try:
                    s = ephem.star(anchor)
                    s.compute(obs)
                    if s.alt > 0: # Если звезда-якорь над горизонтом
                        visible_targets.append((constellations_db[key], anchor))
                except: pass

        # Выбираем случайную цель из видимых
        if visible_targets:
            target_data, target_star = random.choice(visible_targets)
            # Чистим имя для рамки (убираем латынь и смайлики)
            display_name = target_data['name'].split('(')[0].strip().upper()
            # Формируем крутой факт для Телеграма
            target_fact = f"{target_data['description']} {target_data['secret']}\nСложность поиска: {target_data['difficulty']}"
            full_name_for_button = target_data['name']
        else:
            display_name = "ГЛУБОКИЙ КОСМОС"
            target_star = None
            target_fact = "Сегодня небо скрыто или нет известных созвездий в зените."
            full_name_for_button = "Космос"

        # 3. ОТРИСОВКА КАРТИНКИ
        bg_img = Image.open('background1.png')
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)

        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(bg_img)
        ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none')
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.axis('off')

        # Фоновые звезды
        np.random.seed(int(float(lat) * 100))
        fx = np.random.uniform(0, 2*np.pi, 3000)
        fy = np.random.uniform(0, np.pi/2, 3000)
        sizes = np.random.uniform(0.5, 3.0, 3000)
        ax.scatter(fx, fy, s=sizes, c='#D4E6FF', alpha=0.8, edgecolors='none')

        # Стандартные линии созвездий-ориентиров
        c_color = '#FFD700'
        uma = ['Alkaid', 'Mizar', 'Alioth', 'Megrez', 'Phecda', 'Merak', 'Dubhe']
        for i in range(len(uma)-1): draw_line(ax, obs, uma[i], uma[i+1], color=c_color, lw=1)
        cas = ['Segin', 'Ruchbah', 'Gamma Cassiopeiae', 'Schedar', 'Caph']
        for i in range(len(cas)-1): draw_line(ax, obs, cas[i], cas[i+1], color=c_color, lw=1)
        
        o_color = '#4DA8DA'
        draw_line(ax, obs, 'Betelgeuse', 'Bellatrix', color=o_color, lw=1)
        draw_line(ax, obs, 'Bellatrix', 'Rigel', color=o_color, lw=1)
        draw_line(ax, obs, 'Rigel', 'Saiph', color=o_color, lw=1)
        draw_line(ax, obs, 'Saiph', 'Betelgeuse', color=o_color, lw=1)

        # Луна
        moon = ephem.Moon()
        moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=350, c='#F4F6F0', alpha=0.9)

        # --- ОТРИСОВКА ЦЕЛИ (КРАСНЫЙ НЕОН) ---
        if target_star:
            try:
                s = ephem.star(target_star)
                s.compute(obs)
                # Рисуем саму звезду ярко-красным
                ax.scatter(s.az, np.pi/2 - s.alt, s=150, c='#FF3366', zorder=10)
                # Рисуем большое неоновое свечение (halo)
                ax.scatter(s.az, np.pi/2 - s.alt, s=700, c='#FF3366', alpha=0.3, zorder=9)
                # Подписываем
                ax.text(s.az, np.pi/2 - s.alt + 0.08, f" [ ЦЕЛЬ ]", color='#FF3366', fontsize=12, fontweight='bold', zorder=11)
            except: pass

        # 4. ВПЕЧАТЫВАЕМ ТЕКСТ (Идеальная калибровка сохранена!)
        sun = ephem.Sun()
        next_rise = ephem.localtime(obs.next_rising(sun)).strftime('%H:%M')
        next_set = ephem.localtime(obs.next_setting(sun)).strftime('%H:%M')

        t_color = '#D4E6FF'
        f_size = 22 

        fig.text(0.38, 0.170, user_name.upper(), color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.49, 0.135, f"{float(lat):.2f}°N, {float(lon):.2f}°E", color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.38, 0.106, get_moon_phase(obs), color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.40, 0.067, next_rise, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.74, 0.067, next_set, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        
        # ДИНАМИЧЕСКОЕ ИМЯ ЦЕЛИ В РАМКУ!
        fig.text(0.38, 0.028, display_name, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)

        # Возвращаем все данные в main.py
        return True, path, full_name_for_button, target_fact
    except Exception as e:
        return False, f"Ошибка отрисовки: {str(e)}", "", ""
