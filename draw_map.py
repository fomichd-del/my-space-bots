import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random
from PIL import Image
import ephem
import warnings

# Отключаем лишние предупреждения Pandas в логах
warnings.filterwarnings("ignore", category=FutureWarning)

# --- ПОЛНЫЙ ЛИНГВИСТИЧЕСКИЙ МОДУЛЬ ---
RU_NAMES = {
    "Andromeda": "Андромеда", "Aquarius": "Водолей", "Aquila": "Орел", "Aries": "Овен",
    "Auriga": "Возничий", "Bootes": "Волопас", "Cancer": "Рак", "Canis Major": "Большой Пес",
    "Canis Minor": "Малый Пес", "Capricornus": "Козерог", "Cassiopeia": "Кассиопея",
    "Cepheus": "Цефей", "Cygnus": "Лебедь", "Draco": "Дракон", "Gemini": "Близнецы",
    "Hercules": "Геркулес", "Leo": "Лев", "Libra": "Весы", "Lyra": "Лира",
    "Ophiuchus": "Змееносец", "Orion": "Орион", "Pegasus": "Пегас", "Perseus": "Персей",
    "Pisces": "Рыбы", "Sagittarius": "Стрелец", "Scorpius": "Скорпион", "Taurus": "Телец",
    "Ursa Major": "Большая Медведица", "Ursa Minor": "Малая Медведица", "Virgo": "Дева",
    "Vega": "Вега", "Polaris": "Полярная", "Sirius": "Сириус", "Arcturus": "Арктур", "Capella": "Капелла", "Altair": "Альтаир"
}

TARGETS = {
    "ursa_major": [165, 56], "ursa_minor": [37, 89], "orion": [84, -5],
    "cassiopeia": [10, 59], "cygnus": [310, 45], "lyra": [279, 39],
    "andromeda": [10, 41], "leo": [152, 12], "gemini": [114, 28],
    "taurus": [69, 16], "aries": [31, 23]
}

def generate_star_map(lat, lon, user_name):
    try:
        dt = datetime.now(timezone.utc)
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        target_key = random.choice(list(TARGETS.keys()))
        target_pos = TARGETS[target_key]
        target_name_rus = db.get(target_key, {}).get('name', target_key).split('(')[0].strip().upper()

        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        
        # Оптимальные шрифты для 1600px
        try:
            style.star.label.font_size = 10
            style.constellation.label.font_size = 14
            style.constellation.line.stroke_width = 2.0
        except: pass

        # resolution=1600 - золотая середина между качеством и скоростью
        p = ZenithPlot(observer=observer, style=style, resolution=1600, autoscale=True)

        p.horizon(); p.milky_way(); p.ecliptic(); p.constellations()

        labels = p.constellation_labels()
        if labels:
            for l in labels:
                if l.text in RU_NAMES: l.text = RU_NAMES[l.text]

        p.stars(where=[_.magnitude < 5.0], where_labels=[_.magnitude < 2.2])
        p.planets(); p.sun(label="СОЛНЦЕ"); p.moon(label="ЛУНА")

        p.marker(
            ra=target_pos[0], dec=target_pos[1],
            label="[ ЦЕЛЬ ]",
            style={
                "marker": {"size": 70, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 3, "line_style": [1, [5, 5]]},
                "label": {"font_size": 22, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 45}
            }
        )

        temp_file = "zenith_v14_1.png"
        p.export(temp_file, transparent=True, padding=0.02)

        # СБОРКА И ЦЕНТРОВКА (X, Y подобраны под background1.png)
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA").resize((1040, 1040))
        bg_img.paste(sky_img, (200, 360), sky_img)

        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        # Рамки текста (22px)
        t_col = '#D4E6FF'
        fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_stable_v14_1.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0); plt.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        return True, path, target_name_rus, ""

    except Exception as e:
        return False, str(e), "", ""
