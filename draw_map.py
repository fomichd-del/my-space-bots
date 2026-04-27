import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os, json, random
from PIL import Image

# Словарь перевода звезд (Только те, что Ephem точно знает)
STAR_NAMES = {
    "Dubhe": "Дубхе", "Merak": "Мерак", "Phecda": "Фекда", "Megrez": "Мегрец", "Alioth": "Алиот", "Mizar": "Мицар", "Alkaid": "Бенетнаш",
    "Polaris": "Полярная", "Kochab": "Кохаб", "Betelgeuse": "Бетельгейзе", "Rigel": "Ригель", "Bellatrix": "Беллатрикс",
    "Alnitak": "Альнитак", "Alnilam": "Альнилам", "Mintaka": "Минтака", "Schedar": "Шедар", "Caph": "Каф", "Regulus": "Регул", 
    "Denebola": "Денебола", "Deneb": "Денеб", "Pollux": "Поллукс", "Castor": "Кастор", "Aldebaran": "Альдебаран", "Elnath": "Элнат", 
    "Markab": "Маркаб", "Alpheratz": "Альферац", "Vega": "Вега", "Procyon": "Процион", "Altair": "Альтаир", "Spica": "Спика", "Arcturus": "Арктур"
}

# Якоря для целей (Используем только надежные звезды)
ANCHOR_STARS = {
    "ursa_major": "Dubhe", "ursa_minor": "Polaris", "orion": "Betelgeuse", "cassiopeia": "Schedar",
    "leo": "Regulus", "cygnus": "Deneb", "gemini": "Pollux", "taurus": "Aldebaran",
    "lyra": "Vega", "aquila": "Altair", "virgo": "Spica", "bootes": "Arcturus", "pegasus": "Markab"
}

# Атлас линий (Золотой стандарт)
CONSTELLATION_LINES = {
    "ursa_major": [("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid")],
    "ursa_minor": [("Polaris", "Kochab"), ("Kochab", "Pherkad"), ("Pherkad", "Zeta Ursae Minoris"), ("Zeta Ursae Minoris", "Polaris")],
    "orion": [("Betelgeuse", "Bellatrix"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"), ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka")],
    "cassiopeia": [("Segin", "Ruchbah"), ("Ruchbah", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Schedar"), ("Schedar", "Caph")],
    "leo": [("Regulus", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), ("Regulus", "Denebola"), ("Denebola", "Zosma"), ("Zosma", "Algieba")],
    "cygnus": [("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Sadr", "Delta Cygni")],
    "gemini": [("Pollux", "Castor"), ("Pollux", "Alhena"), ("Castor", "Mebsuta")],
    "taurus": [("Aldebaran", "Elnath"), ("Aldebaran", "Zeta Tauri")],
    "pegasus": [("Markab", "Scheat"), ("Scheat", "Alpheratz"), ("Alpheratz", "Algenib"), ("Algenib", "Markab")]
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
                # Двойная отрисовка для Glow эффекта
                ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=alpha, zorder=3)
                ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw*3, alpha=alpha*0.3, zorder=2)
                coords.append((s1.az, np.pi/2 - s1.alt))
        except: pass
    
    # Названия каждой звезды в созвездии
    for s_name in unique_stars:
        try:
            st = ephem.star(s_name)
            st.compute(obs)
            if st.alt > 0:
                ax.scatter(st.az, np.pi/2 - st.alt, s=20 if is_target else 10, c='white', edgecolors=color, linewidth=0.5, zorder=4)
                name_rus = STAR_NAMES.get(s_name, s_name)
                ax.text(st.az, np.pi/2 - st.alt + 0.05, name_rus, color='white', fontsize=7, alpha=0.6, ha='center', zorder=5)
        except: pass

    # Общее название созвездия
    if coords and const_name:
        avg_az = np.mean([c[0] for c in coords])
        avg_alt = np.mean([c[1] for c in coords])
        ax.text(avg_az, avg_alt - 0.15, const_name, color=color, fontsize=12 if is_target else 9, fontweight='bold', ha='center', zorder=6)

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer(); obs.lat, obs.lon = str(lat), str(lon); obs.date = datetime.utcnow()
        with open('constellations.json', 'r', encoding='utf-8') as f: db = json.load(f)
        
        # Фильтр: берем созвездия из АТЛАСА ЛИНИЙ, которые сейчас видны
        visible_keys = []
        for k in CONSTELLATION_LINES.keys():
            if k in ANCHOR_STARS:
                try:
                    s = ephem.star(ANCHOR_STARS[k])
                    s.compute(obs)
                    if s.alt > 0: visible_keys.append(k)
                except: pass
        
        target_key = random.choice(visible_keys) if visible_keys else "ursa_major"

        bg_img = Image.open('background1.png')
        dpi = 100; fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none'); ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.axis('off')

        # Фон (пыль)
        np.random.seed(int(float(lat)*100))
        ax.scatter(np.random.uniform(0, 2*np.pi, 2000), np.random.uniform(0, np.pi/2, 2000), s=np.random.uniform(0.3, 1.3), c='white', alpha=0.3)

        # Отрисовка всех созвездий из атласа
        for cid, lines in CONSTELLATION_LINES.items():
            is_target = (cid == target_key)
            name = db[cid]['name'].split('(')[0].strip().upper() if cid in db else cid.upper()
            draw_constellation(ax, obs, lines, '#FF00FF' if is_target else '#FFD700', 5.0 if is_target else 1.8, 0.9 if is_target else 0.4, name, is_target)

        # Луна
        moon = ephem.Moon(); moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=400, c='#F4F6F0', edgecolors='white', alpha=0.9, zorder=7)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.15, f"ЛУНА ({int(moon.phase)}%)", color='white', fontsize=10, fontweight='bold', ha='center')

        # Солнце
        sun = ephem.Sun(); sun.compute(obs)
        if sun.alt > -0.2:
            ax.scatter(sun.az, np.pi/2 - sun.alt, s=600, c='#FFCC33', edgecolors='#FF6600', zorder=7)
            ax.text(sun.az, np.pi/2 - sun.alt + 0.2, "СОЛНЦЕ", color='#FFCC33', fontsize=12, fontweight='bold', ha='center')

        # Планеты
        for p, sym, n, c in [(ephem.Mars(), "♂", "МАРС", "#FF4500"), (ephem.Jupiter(), "♃", "ЮПИТЕР", "#4DA8DA")]:
            try:
                p.compute(obs)
                if p.alt > 0:
                    ax.scatter(p.az, np.pi/2 - p.alt, s=180, c=c, edgecolors='white', zorder=6)
                    ax.text(p.az, np.pi/2 - p.alt - 0.15, f"{sym} {n}", color=c, fontsize=12, fontweight='bold', ha='center')
            except: pass

        # Финальный текст (Твоя калибровка 22px)
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
