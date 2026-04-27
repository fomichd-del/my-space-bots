import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os, json, random
from PIL import Image

# Перевод имен звезд для подписей
STAR_TRANSLATIONS = {
    "Alpheratz": "Альферац", "Sadalmelik": "Садальмелик", "Altair": "Альтаир", "Hamal": "Хамаль",
    "Capella": "Капелла", "Arcturus": "Арктур", "Sirius": "Сириус", "Procyon": "Процион",
    "Deneb Algedi": "Денеб Альгеди", "Schedar": "Шедар", "Alderamin": "Альдерамин", "Deneb": "Денеб",
    "Thuban": "Тубан", "Pollux": "Поллукс", "Castor": "Кастор", "Regulus": "Регул", "Vega": "Вега",
    "Betelgeuse": "Бетельгейзе", "Rigel": "Ригель", "Markab": "Маркаб", "Mirfak": "Мирфак",
    "Nunki": "Нунки", "Antares": "Антарес", "Aldebaran": "Альдебаран", "Dubhe": "Дубхе", "Merak": "Мерак",
    "Phecda": "Фекда", "Megrez": "Мегрец", "Alioth": "Алиот", "Mizar": "Мицар", "Alkaid": "Бенетнаш",
    "Polaris": "Полярная", "Kochab": "Кохаб", "Bellatrix": "Беллатрикс", "Alnitak": "Альнитак",
    "Spica": "Спика", "Alhena": "Альхена", "Sadr": "Садр", "Albireo": "Альбирео"
}

ANCHOR_STARS = {
    "andromeda": "Alpheratz", "aquarius": "Sadalmelik", "aquila": "Altair", "aries": "Hamal",
    "auriga": "Capella", "bootes": "Arcturus", "canis_major": "Sirius", "canis_minor": "Procyon",
    "capricornus": "Deneb Algedi", "cassiopeia": "Schedar", "cepheus": "Alderamin", "cygnus": "Deneb",
    "draco": "Thuban", "gemini": "Pollux", "hercules": "Rasalgethi", "leo": "Regulus",
    "lyra": "Vega", "orion": "Betelgeuse", "pegasus": "Markab", "perseus": "Mirfak",
    "sagittarius": "Nunki", "scorpius": "Antares", "taurus": "Aldebaran", "ursa_major": "Dubhe",
    "ursa_minor": "Polaris", "virgo": "Spica"
}

CONSTELLATION_LINES = {
    "ursa_major": [("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid")],
    "ursa_minor": [("Polaris", "Kochab"), ("Kochab", "Pherkad"), ("Pherkad", "Zeta Ursae Minoris"), ("Zeta Ursae Minoris", "Polaris")],
    "orion": [("Betelgeuse", "Bellatrix"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"), ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka")],
    "cassiopeia": [("Segin", "Ruchbah"), ("Ruchbah", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Schedar"), ("Schedar", "Caph")],
    "leo": [("Regulus", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), ("Regulus", "Denebola"), ("Denebola", "Zosma"), ("Zosma", "Algieba")],
    "cygnus": [("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Sadr", "Delta Cygni")],
    "gemini": [("Pollux", "Castor"), ("Pollux", "Alhena"), ("Castor", "Mebsuta")],
    "taurus": [("Aldebaran", "Elnath"), ("Aldebaran", "Zeta Tauri")]
}

def get_moon_phase_info(obs):
    m = ephem.Moon(obs)
    return int(m.phase)

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer(); obs.lat, obs.lon = str(lat), str(lon); obs.date = datetime.utcnow()
        with open('constellations.json', 'r', encoding='utf-8') as f: db = json.load(f)
        
        visible = [k for k, v in ANCHOR_STARS.items() if ephem.star(v).compute(obs) or True]
        target_key = random.choice(visible) if visible else "ursa_major"

        bg_img = Image.open('background1.png')
        dpi = 100; fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none'); ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.axis('off')

        # 1. Фон (звездная пыль)
        np.random.seed(int(float(lat)*100))
        ax.scatter(np.random.uniform(0, 2*np.pi, 1500), np.random.uniform(0, np.pi/2, 1500), s=1, c='white', alpha=0.3)

        # 2. Отрисовка созвездий (Линии + Названия звезд)
        for cid, lines in CONSTELLATION_LINES.items():
            is_target = (cid == target_key)
            color = '#FF00FF' if is_target else '#FFD700' # Розовый неон для цели
            alpha = 1.0 if is_target else 0.5
            lw = 6.0 if is_target else 1.8 # Очень жирные линии для цели

            unique_stars = set()
            for s1_n, s2_n in lines:
                unique_stars.add(s1_n); unique_stars.add(s2_n)
                try:
                    s1, s2 = ephem.star(s1_n), ephem.star(s2_n)
                    s1.compute(obs); s2.compute(obs)
                    if s1.alt > 0 and s2.alt > 0:
                        # Рисуем линию (свечение)
                        ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=alpha, zorder=3)
                        if is_target: # Дополнительное свечение для цели
                            ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw*2, alpha=0.2, zorder=2)
                except: pass

            # Подписи каждой звезды
            for s_name in unique_stars:
                try:
                    star = ephem.star(s_name)
                    star.compute(obs)
                    if star.alt > 0:
                        # Точка звезды
                        ax.scatter(star.az, np.pi/2 - star.alt, s=40 if is_target else 15, c='white', edgecolors=color, zorder=4)
                        # Название звезды (меньше чем созвездие)
                        rus_star = STAR_TRANSLATIONS.get(s_name, s_name)
                        ax.text(star.az, np.pi/2 - star.alt + 0.05, rus_star, color='white', fontsize=7, alpha=0.8, ha='center', zorder=5)
                except: pass

            # Название созвездия (крупно в центре)
            if cid in db:
                name = db[cid]['name'].split('(')[0].strip().upper()
                anchor = ephem.star(ANCHOR_STARS[cid])
                anchor.compute(obs)
                ax.text(anchor.az, np.pi/2 - anchor.alt - 0.15, name, color=color, fontsize=14 if is_target else 9, fontweight='bold', ha='center', zorder=6)

        # 3. Ориентиры (Солнце, Луна, Планеты)
        moon = ephem.Moon(); moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=400, c='#F4F6F0', edgecolors='white', zorder=7)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.15, f"ЛУНА ({int(moon.phase)}%)", color='white', fontsize=10, fontweight='bold', ha='center')

        sun = ephem.Sun(); sun.compute(obs)
        if sun.alt > -0.2:
            ax.scatter(sun.az, np.pi/2 - sun.alt, s=500, c='#FFCC33', edgecolors='#FF6600', zorder=7)
            ax.text(sun.az, np.pi/2 - sun.alt + 0.18, "СОЛНЦЕ", color='#FFCC33', fontsize=12, fontweight='bold', ha='center')

        # Планеты
        for p, n, c in [(ephem.Mars(), "♂ МАРС", "#FF4500"), (ephem.Jupiter(), "♃ ЮПИТЕР", "#4DA8DA")]:
            p.compute(obs)
            if p.alt > 0:
                ax.scatter(p.az, np.pi/2 - p.alt, s=150, c=c, edgecolors='white', zorder=6)
                ax.text(p.az, np.pi/2 - p.alt - 0.12, n, color=c, fontsize=12, fontweight='bold', ha='center')

        # 4. Текст в рамках (Калибровка штурмана)
        t_key = target_key if target_key in db else "ursa_major"
        target_name = db[t_key]['name'].split('(')[0].strip().upper()
        rise = ephem.localtime(obs.next_rising(ephem.Sun())).strftime('%H:%M')
        sset = ephem.localtime(obs.next_setting(ephem.Sun())).strftime('%H:%M')

        fig.text(0.38, 0.170, user_name.upper(), color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"Фаза: {int(moon.phase)}%", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, sset, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0, facecolor='#0B0D14')
        plt.close(); return True, path, target_name, ""
    except Exception as e: return False, str(e), "", ""
