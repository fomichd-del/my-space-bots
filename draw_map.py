import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random
from PIL import Image
import ephem

# --- ЛИНГВИСТИЧЕСКИЙ МОДУЛЬ ---
CONSTELLATION_RU = {
    "Andromeda": "Андромеда", "Aquarius": "Водолей", "Aquila": "Орел", "Aries": "Овен",
    "Auriga": "Возничий", "Bootes": "Волопас", "Cancer": "Рак", "Canis Major": "Большой Пес",
    "Canis Minor": "Малый Пес", "Capricornus": "Козерог", "Cassiopeia": "Кассиопея",
    "Cepheus": "Цефей", "Cygnus": "Лебедь", "Draco": "Дракон", "Gemini": "Близнецы",
    "Hercules": "Геркулес", "Leo": "Лев", "Libra": "Весы", "Lyra": "Лира",
    "Ophiuchus": "Змееносец", "Orion": "Орион", "Pegasus": "Пегас", "Perseus": "Персей",
    "Pisces": "Рыбы", "Sagittarius": "Стрелец", "Scorpius": "Скорпион", "Taurus": "Телец",
    "Ursa Major": "Большая Медведица", "Ursa Minor": "Малая Медведица", "Virgo": "Дева"
}

TARGETS = {
    "ursa_major": [165, 56], "ursa_minor": [37, 89], "orion": [84, -5],
    "cassiopeia": [10, 59], "leo": [152, 12], "cygnus": [310, 45],
    "gemini": [114, 28], "taurus": [69, 16], "lyra": [279, 39]
}

def generate_star_map(lat, lon, user_name):
    try:
        # 1. Время с часовым поясом (обязательно для Starplot)
        dt = datetime.now(timezone.utc)
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        target_key = random.choice(list(TARGETS.keys()))
        target_pos = TARGETS[target_key]
        target_name_rus = db[target_key]['name'].split('(')[0].strip().upper()

        # 2. Стиль
        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        
        # Безопасная настройка атрибутов
        try:
            style.star.label.font_size = 12
            style.constellation.label.font_size = 18
            style.constellation.line.stroke_width = 3
            style.planet.label.font_size = 16
        except: pass

        p = ZenithPlot(observer=observer, style=style, resolution=2600, autoscale=True)

        # 3. Отрисовка
        p.horizon()
        p.milky_way()
        p.ecliptic()
        p.constellations()

        # ИСПРАВЛЕНИЕ: Безопасная итерация по ярлыкам
        labels = p.constellation_labels()
        if labels is not None:
            for label in labels:
                if label.text in CONSTELLATION_RU:
                    label.text = CONSTELLATION_RU[label.text]

        p.stars(where=[_.magnitude < 5.5], where_labels=[_.magnitude < 2.5])
        p.planets()
        p.sun(label="СОЛНЦЕ")
        p.moon(label="ЛУНА")

        # 4. Маркер цели
        p.marker(
            ra=target_pos[0], dec=target_pos[1],
            label="[ ЦЕЛЬ ]",
            style={
                "marker": {"size": 95, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 4, "line_style": [1, [6, 6]]},
                "label": {"font_size": 28, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 65}
            }
        )

        temp_file = "zenith_v12_4.png"
        p.export(temp_file, transparent=True, padding=0.1)

        # 5. Сборка на фоне
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA").resize((1060, 1060))
        bg_img.paste(sky_img, (200, 360), sky_img)

        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        # ВОЗВРАТ РАСЧЕТОВ EPHEM ДЛЯ РАМОК
        e_obs = ephem.Observer()
        e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), dt.strftime('%Y/%m/%d %H:%M:%S')
        moon, sun = ephem.Moon(), ephem.Sun()
        moon.compute(e_obs); sun.compute(e_obs)
        
        # Безопасный расчет восхода/заката
        try:
            rise = ephem.localtime(e_obs.next_rising(sun)).strftime('%H:%M')
            sset = ephem.localtime(e_obs.next_setting(sun)).strftime('%H:%M')
        except:
            rise, sset = "--:--", "--:--"

        # Текст (22px калибровка)
        t_col = '#D4E6FF'
        fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"Фаза: {int(moon.phase)}%", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise, color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, sset, color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_stable_v12_4.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0); plt.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        return True, path, target_name_rus, ""

    except Exception as e:
        return False, str(e), "", ""
