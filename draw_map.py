import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os, json, random
from PIL import Image

# Словарь перевода звезд для карты
STAR_NAMES = {
    "Dubhe": "Дубхе", "Merak": "Мерак", "Phecda": "Фекда", "Megrez": "Мегрец", "Alioth": "Алиот", "Mizar": "Мицар", "Alkaid": "Бенетнаш",
    "Polaris": "Полярная", "Kochab": "Кохаб", "Pherkad": "Феркад", "Betelgeuse": "Бетельгейзе", "Rigel": "Ригель", "Bellatrix": "Беллатрикс",
    "Saiph": "Саиф", "Alnitak": "Альнитак", "Alnilam": "Альнилам", "Mintaka": "Минтака", "Segin": "Сегин", "Ruchbah": "Рукбах",
    "Gamma Cassiopeiae": "Нави", "Schedar": "Шедар", "Caph": "Каф", "Regulus": "Регул", "Algieba": "Альгиеба", "Denebola": "Денебола",
    "Deneb": "Денеб", "Sadr": "Садр", "Albireo": "Альбирео", "Pollux": "Поллукс", "Castor": "Кастор", "Alhena": "Альхена",
    "Aldebaran": "Альдебаран", "Elnath": "Элнат", "Markab": "Маркаб", "Scheat": "Шеат", "Alpheratz": "Альферац", "Algenib": "Альгениб",
    "Vega": "Вега", "Sheliak": "Шелиак", "Sulafat": "Сулафат", "Procyon": "Процион", "Gomeisa": "Гомейса", "Altair": "Альтаир",
    "Tarazed": "Таразед", "Alshain": "Альшаин", "Spica": "Спика", "Arcturus": "Арктур"
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

# Продвинутый атлас линий
CONSTELLATION_LINES = {
    "ursa_major": [("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid")],
    "ursa_minor": [("Polaris", "Kochab"), ("Kochab", "Pherkad"), ("Pherkad", "Zeta Ursae Minoris"), ("Zeta Ursae Minoris", "Polaris")],
    "orion": [("Betelgeuse", "Bellatrix"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"), ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka")],
    "cassiopeia": [("Segin", "Ruchbah"), ("Ruchbah", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Schedar"), ("Schedar", "Caph")],
    "leo": [("Regulus", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), ("Regulus", "Denebola"), ("Denebola", "Zosma"), ("Zosma", "Algieba")],
    "cygnus": [("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Sadr", "Delta Cygni")],
    "gemini": [("Pollux", "Castor"), ("Pollux", "Alhena"), ("Castor", "Mebsuta")],
    "taurus": [("Aldebaran", "Elnath"), ("Aldebaran", "Zeta Tauri")],
    "canis_minor": [("Procyon", "Gomeisa")],
    "lyra": [("Vega", "Sheliak"), ("Sheliak", "Sulafat"), ("Sulafat", "Vega")]
}

def draw_constellation(ax, obs, lines, color, lw, alpha, const_name, is_target):
    coords = []
    unique_stars = set()
    for s1_n, s2_n in lines:
        unique_stars.add(s1_n); unique_stars.add(s2_n)
        try:
            s1, s2 = ephem.star(s1_n), ephem.star(s2_n)
            s1.compute(obs); s2.compute(obs)
            if s1.alt > 0 and s2.alt > 0:
                # Рисуем линию (Glow эффект через 2 слоя)
                ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=alpha, zorder=3)
                ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw*2.5, alpha=alpha*0.3, zorder=2)
                coords.append((s1.az, np.pi/2 - s1.alt))
        except: pass
    
    # Названия каждой звезды
    for s_name in unique_stars:
        try:
            st = ephem.star(s_name)
            st.compute(obs)
            if st.alt > 0:
                ax.scatter(st.az, np.pi/2 - st.alt, s=25 if is_target else 10, c='white', edgecolors=color, zorder=4)
                ax.text(st.az, np.pi/2 - st.alt + 0.04, STAR_NAMES.get(s_name, s_name), color='white', fontsize=7, alpha=0.7, ha='center', zorder=5)
        except: pass

    # Название созвездия
    if coords and const_name:
        avg_az = np.mean([c[0] for c in coords])
        avg_alt = np.mean([c[1] for c in coords])
        ax.text(avg_az, avg_alt - 0.1, const_name, color=color, fontsize=12 if is_target else 9, fontweight='bold', ha='center', zorder=6)

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer(); obs.lat, obs.lon = str(lat), str(lon); obs.date = datetime.utcnow()
        with open('constellations.json', 'r', encoding='utf-8') as f: db = json.load(f)
        
        visible = [k for k, v in ANCHOR_STARS.items() if ephem.star(v).compute(obs) or True]
        target_key = random.choice(visible) if visible else "ursa_major"

        if not os.path.exists('background1.png'): return False, "Файл background1.png не найден!", "", ""
        bg_img = Image.open('background1.png')
        dpi = 100; fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none'); ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.axis('off')

        # Звездная пыль
        np.random.seed(int(float(lat)*100))
        ax.scatter(np.random.uniform(0, 2*np.pi, 2500), np.random.uniform(0, np.pi/2, 2500), s=np.random.uniform(0.3, 1.5), c='white', alpha=0.25)

        # Рисуем все созвездия
        for cid, lines in CONSTELLATION_LINES.items():
            is_target = (cid == target_key)
            name = db[cid]['name'].split('(')[0].strip().upper() if cid in db else ""
            draw_constellation(ax, obs, lines, '#FF00FF' if is_target else '#FFD700', 4.5 if is_target else 1.8, 0.9 if is_target else 0.4, name, is_target)

        # Луна
        moon = ephem.Moon(); moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=400, c='#F4F6F0', edgecolors='white', zorder=7)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.15, f"ЛУНА ({int(moon.phase)}%)", color='white', fontsize=10, fontweight='bold', ha='center')

        # Солнце
        sun = ephem.Sun(); sun.compute(obs)
        if sun.alt > -0.2:
            ax.scatter(sun.az, np.pi/2 - sun.alt, s=500, c='#FFCC33', edgecolors='#FF6600', zorder=7)
            ax.text(sun.az, np.pi/2 - sun.alt + 0.15, "СОЛНЦЕ", color='#FFCC33', fontsize=11, fontweight='bold', ha='center')

        # Планеты (Символы)
        for p, sym, n, c in [(ephem.Mars(), "♂", "МАРС", "#FF4500"), (ephem.Jupiter(), "♃", "ЮПИТЕР", "#4DA8DA")]:
            p.compute(obs)
            if p.alt > 0:
                ax.scatter(p.az, np.pi/2 - p.alt, s=150, c=c, edgecolors='white', zorder=6)
                ax.text(p.az, np.pi/2 - p.alt - 0.12, f"{sym} {n}", color=c, fontsize=12, fontweight='bold', ha='center')

        # Текст (Калибровка 22px)
        t_key = target_key if target_key in db else "ursa_major"
        target_name = db[t_key]['name'].split('(')[0].strip().upper()
        rise = ephem.localtime(obs.next_rising(ephem.Sun())).strftime('%H:%M')
        sset = ephem.localtime(obs.next_setting(ephem.Sun())).strftime('%H:%M')

        fig.text(0.38, 0.170, user_name.upper(), color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"Растущая ({int(moon.phase)}%)", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, sset, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0, facecolor='#0B0D14')
        plt.close(); return True, path, target_name, ""
    except Exception as e: return False, str(e), "", ""
