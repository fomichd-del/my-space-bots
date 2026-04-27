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

# Звезды-Якоря для наведения прицела
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
        elif p < 0.55: return "1-я четверть"
        elif p < 0.95: return f"Растущая ({int(p*100)}%)"
        else: return "Полнолуние"
    except: return "Расчет..."

def draw_line(ax, obs, star1, star2, color='white', lw=1):
    try:
        s1, s2 = ephem.star(star1), ephem.star(star2)
        s1.compute(obs)
        s2.compute(obs)
        if s1.alt > 0 and s2.alt > 0:
            ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=0.6)
    except: pass

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()

        # Загрузка базы
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        # Выбор цели
        visible = []
        for key, anchor in ANCHOR_STARS.items():
            if key in db:
                try:
                    s = ephem.star(anchor)
                    s.compute(obs)
                    if s.alt > 0: visible.append(key)
                except: pass
        
        target_key = random.choice(visible) if visible else None
        
        # Рендеринг
        bg_img = Image.open('background1.png')
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(bg_img)
        ax_bg.axis('off')

        # Слой неба (твоя калибровка)
        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none')
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.axis('off')

        # Звезды
        np.random.seed(int(float(lat)*100))
        fx = np.random.uniform(0, 2*np.pi, 2500)
        fy = np.random.uniform(0, np.pi/2, 2500)
        ax.scatter(fx, fy, s=np.random.uniform(0.5, 3), c='#D4E6FF', alpha=0.6)

        # Ориентиры (Медведицы, Орион)
        c_color = '#FFD700'
        uma = ['Alkaid', 'Mizar', 'Alioth', 'Megrez', 'Phecda', 'Merak', 'Dubhe']
        for i in range(len(uma)-1): draw_line(ax, obs, uma[i], uma[i+1], color=c_color)

        # ПОДСВЕТКА ЦЕЛИ
        target_name = "ГЛУБОКИЙ КОСМОС"
        target_fact = "Космос полон тайн!"
        if target_key:
            anchor_name = ANCHOR_STARS[target_key]
            s = ephem.star(anchor_name)
            s.compute(obs)
            ax.scatter(s.az, np.pi/2 - s.alt, s=150, c='#FF3366', edgecolors='white', zorder=10)
            ax.text(s.az, np.pi/2 - s.alt + 0.08, " [ЦЕЛЬ]", color='#FF3366', fontweight='bold')
            target_name = db[target_key]['name'].split('(')[0].strip().upper()
            target_fact = f"{db[target_key]['description']}\n{db[target_key]['secret']}"

        # Текст (твоя идеальная калибровка)
        sun = ephem.Sun()
        next_rise = ephem.localtime(obs.next_rising(sun)).strftime('%H:%M')
        next_set = ephem.localtime(obs.next_setting(sun)).strftime('%H:%M')
        t_color = '#D4E6FF'
        f_size = 22

        fig.text(0.38, 0.170, user_name.upper(), color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.38, 0.106, get_moon_phase(obs), color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.40, 0.067, next_rise, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.74, 0.067, next_set, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.38, 0.028, target_name, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        return True, path, target_name, target_fact
    except Exception as e:
        return False, str(e), None, None
