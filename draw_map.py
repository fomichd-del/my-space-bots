import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os, json, random
from PIL import Image

STAR_NAMES = {
    "Dubhe": "Дубхе", "Merak": "Мерак", "Phecda": "Фекда", "Megrez": "Мегрец", "Alioth": "Алиот", "Mizar": "Мицар", "Alkaid": "Бенетнаш",
    "Polaris": "Полярная", "Kochab": "Кохаб", "Pherkad": "Феркад", "Betelgeuse": "Бетельгейзе", "Rigel": "Ригель", "Bellatrix": "Беллатрикс",
    "Saiph": "Саиф", "Alnitak": "Альнитак", "Alnilam": "Альнилам", "Mintaka": "Минтака", "Schedar": "Шедар", "Caph": "Каф", "Regulus": "Регул", 
    "Denebola": "Денебола", "Deneb": "Денеб", "Pollux": "Поллукс", "Castor": "Кастор", "Aldebaran": "Альдебаран", "Elnath": "Элнат", 
    "Markab": "Маркаб", "Alpheratz": "Альферац", "Vega": "Вега", "Procyon": "Процион", "Altair": "Альтаир", "Spica": "Спика", "Arcturus": "Арктур"
}

ANCHOR_STARS = {
    "ursa_major": "Dubhe", "ursa_minor": "Polaris", "orion": "Betelgeuse", "cassiopeia": "Schedar",
    "leo": "Regulus", "cygnus": "Deneb", "gemini": "Pollux", "taurus": "Aldebaran", "lyra": "Vega"
}

# МАКСИМАЛЬНО ПОЛНЫЙ АТЛАС (Достроены все "хвосты" и "ноги")
CONSTELLATION_LINES = {
    "ursa_major": [
        ("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), 
        ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid")
    ],
    "ursa_minor": [
        ("Polaris", "Delta Ursae Minoris"), ("Delta Ursae Minoris", "Epsilon Ursae Minoris"), 
        ("Epsilon Ursae Minoris", "Zeta Ursae Minoris"), ("Zeta Ursae Minoris", "Kochab"), 
        ("Kochab", "Pherkad"), ("Pherkad", "Zeta Ursae Minoris")
    ],
    "orion": [
        ("Betelgeuse", "Bellatrix"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"),
        ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka"), ("Betelgeuse", "Meissa"), ("Meissa", "Bellatrix")
    ],
    "cassiopeia": [
        ("Caph", "Schedar"), ("Schedar", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Ruchbah"), ("Ruchbah", "Segin")
    ],
    "leo": [
        ("Regulus", "Eta Leonis"), ("Eta Leonis", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), 
        ("Regulus", "Chertan"), ("Chertan", "Denebola"), ("Denebola", "Zosma"), ("Zosma", "Chertan")
    ],
    "cygnus": [
        ("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Sadr", "Delta Cygni"), ("Sadr", "Eta Cygni")
    ],
    "lyra": [("Vega", "Sheliak"), ("Sheliak", "Sulafat"), ("Sulafat", "Delta2 Lyrae"), ("Delta2 Lyrae", "Vega")]
}

def draw_shining_star(ax, az, alt_r, color, size, is_target):
    # Эффект горения (слои)
    glow_size = size * (15 if is_target else 8)
    ax.scatter(az, alt_r, s=glow_size*3, c=color, alpha=0.1, zorder=2) # Гало
    ax.scatter(az, alt_r, s=glow_size, c=color, alpha=0.3, zorder=3)   # Свечение
    ax.scatter(az, alt_r, s=size*2, c='white', zorder=4)              # Ядро
    # Лучи горения (дифракционные шипы)
    ray_color = color if is_target else 'white'
    ax.scatter(az, alt_r, s=glow_size*4, c=ray_color, marker='+', alpha=0.4, linewidths=0.5, zorder=2)
    ax.scatter(az, alt_r, s=glow_size*4, c=ray_color, marker='x', alpha=0.2, linewidths=0.3, zorder=2)

def draw_constellation(ax, obs, lines, color, lw, alpha, name, is_target):
    coords = []
    unique_stars = set()
    for s1_n, s2_n in lines:
        unique_stars.add(s1_n); unique_stars.add(s2_n)
        try:
            s1, s2 = ephem.star(s1_n), ephem.star(s2_n)
            s1.compute(obs); s2.compute(obs)
            if s1.alt > 0 and s2.alt > 0:
                ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=alpha, zorder=3)
                coords.append((s1.az, np.pi/2 - s1.alt))
        except: pass
    
    for s_name in unique_stars:
        try:
            st = ephem.star(s_name); st.compute(obs)
            if st.alt > 0:
                draw_shining_star(ax, st.az, np.pi/2 - st.alt, color, 10, is_target)
                ax.text(st.az, np.pi/2 - st.alt + 0.05, STAR_NAMES.get(s_name, s_name), color='white', fontsize=6, alpha=0.5, ha='center', zorder=5)
        except: pass

    if coords and name:
        avg_az = np.mean([c[0] for c in coords])
        avg_alt = np.mean([c[1] for c in coords])
        ax.text(avg_az, avg_alt - 0.12, name, color=color, fontsize=12 if is_target else 8, fontweight='bold', ha='center', zorder=6)

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer(); obs.lat, obs.lon = str(lat), str(lon); obs.date = datetime.utcnow()
        with open('constellations.json', 'r', encoding='utf-8') as f: db = json.load(f)
        
        visible_keys = [k for k in CONSTELLATION_LINES.keys() if ephem.star(ANCHOR_STARS[k]).compute(obs) or True]
        target_key = random.choice(visible_keys) if visible_keys else "ursa_major"

        bg_img = Image.open('background1.png')
        dpi = 100; fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none'); ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.axis('off')

        # Уплотненная звездная пыль
        np.random.seed(int(float(lat)*100))
        ax.scatter(np.random.uniform(0, 2*np.pi, 4000), np.random.uniform(0, np.pi/2, 4000), s=np.random.uniform(0.1, 1.2), c='white', alpha=0.3)

        for cid, lines in CONSTELLATION_LINES.items():
            is_target = (cid == target_key)
            name = db[cid]['name'].split('(')[0].strip().upper() if cid in db else cid.upper()
            draw_constellation(ax, obs, lines, '#FF00FF' if is_target else '#FFD700', 4.0 if is_target else 1.2, 0.8 if is_target else 0.3, name, is_target)

        moon = ephem.Moon(); moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=400, c='#F4F6F0', edgecolors='white', alpha=0.8, zorder=7)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.15, f"ЛУНА ({int(moon.phase)}%)", color='white', fontsize=10, fontweight='bold', ha='center')

        sun = ephem.Sun(); sun.compute(obs)
        if sun.alt > -0.2:
            ax.scatter(sun.az, np.pi/2 - sun.alt, s=600, c='#FFCC33', edgecolors='#FF6600', zorder=7)

        # Текст
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
