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

# Глушим технический шум в логах
warnings.filterwarnings("ignore", category=FutureWarning)

# --- ПОЛНЫЙ ЛИНГВИСТИЧЕСКИЙ МОДУЛЬ (88 СОЗВЕЗДИЙ) ---
RU_NAMES = {
    "Andromeda": "Андромеда", "Antlia": "Насос", "Apus": "Райская Птица", "Aquarius": "Водолей",
    "Aquila": "Орел", "Ara": "Жертвенник", "Aries": "Овен", "Auriga": "Возничий", "Bootes": "Волопас",
    "Caelum": "Резец", "Camelopardalis": "Жираф", "Cancer": "Рак", "Canes Venatici": "Гончие Псы",
    "Canis Major": "Большой Пес", "Canis Minor": "Малый Пес", "Capricornus": "Козерог",
    "Carina": "Киль", "Cassiopeia": "Кассиопея", "Centaurus": "Центавр", "Cepheus": "Цефей",
    "Cetus": "Кит", "Chamaeleon": "Хамелеон", "Circinus": "Циркуль", "Columba": "Голубь",
    "Coma Berenices": "Волосы Вероники", "Corona Australis": "Южная Корона", "Corona Borealis": "Северная Корона",
    "Corvus": "Ворон", "Crater": "Чаша", "Crux": "Южный Крест", "Cygnus": "Лебедь", "Delphinus": "Дельфин",
    "Dorado": "Золотая Рыба", "Draco": "Дракон", "Equuleus": "Малый Конь", "Eridanus": "Эридан",
    "Fornax": "Печь", "Gemini": "Близнецы", "Grus": "Журавль", "Hercules": "Геркулес", "Horologium": "Часы",
    "Hydra": "Гидра", "Hydrus": "Южная Гидра", "Indus": "Индеец", "Lacerta": "Ящерица", "Leo": "Лев",
    "Leo Minor": "Малый Лев", "Lepus": "Заяц", "Libra": "Весы", "Lupus": "Волк", "Lynx": "Рысь",
    "Lyra": "Лира", "Mensa": "Столовая Гора", "Microscopium": "Микроскоп", "Monoceros": "Единорог",
    "Musca": "Муха", "Norma": "Наугольник", "Octans": "Октант", "Ophiuchus": "Змееносец", "Orion": "Орион",
    "Pavo": "Павлин", "Pegasus": "Пегас", "Perseus": "Персей", "Phoenix": "Феникс", "Pictor": "Живописец",
    "Pisces": "Рыбы", "Piscis Austrinus": "Южная Рыба", "Puppis": "Корма", "Pyxis": "Компас",
    "Reticulum": "Сетка", "Sagitta": "Стрела", "Sagittarius": "Стрелец", "Scorpius": "Скорпион",
    "Sculptor": "Скульптор", "Scutum": "Щит", "Serpens": "Змея", "Sextans": "Секстант", "Taurus": "Телец",
    "Telescopium": "Телескоп", "Triangulum": "Треугольник", "Triangulum Australe": "Южный Треугольник",
    "Tucana": "Тукан", "Ursa Major": "Большая Медведица", "Ursa Minor": "Малая Медведица",
    "Vela": "Паруса", "Virgo": "Дева", "Volans": "Летучая Рыба", "Vulpecula": "Лисичка",
    "Vega": "Вега", "Polaris": "Полярис", "Sirius": "Сириус", "Arcturus": "Арктур", "Capella": "Капелла"
}

TARGETS = {
    "ursa_major": [165, 56], "ursa_minor": [37, 89], "orion": [84, -5],
    "cassiopeia": [10, 59], "cygnus": [310, 45], "lyra": [279, 39],
    "aries": [31, 23], "taurus": [69, 16], "gemini": [114, 28],
    "cancer": [130, 20], "leo": [152, 12], "virgo": [201, -11]
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

        # ШАГ 1: Создаем чистый стиль (Pydantic не видит наших правок здесь)
        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        
        # ШАГ 2: Меняем атрибуты напрямую (используем цифры вместо 'bold')
        try:
            style.star.label.font_size = 12
            style.star.label.font_weight = 500
            
            style.constellation.label.font_size = 18
            style.constellation.label.font_weight = 700  # 700 = Bold
            style.constellation.line.stroke_width = 3.0
            
            style.planet.label.font_size = 16
            style.planet.label.font_weight = 700
        except: pass

        p = ZenithPlot(observer=observer, style=style, resolution=1800, autoscale=True)

        p.horizon(); p.milky_way(); p.ecliptic(); p.constellations()

        # ПЕРЕВОД (88 созвездий)
        labels = p.constellation_labels()
        if labels is not None:
            for l in labels:
                if l.text in RU_NAMES: l.text = RU_NAMES[l.text]

        p.stars(where=[_.magnitude < 5.2], where_labels=[_.magnitude < 2.5])
        p.planets(); p.sun(label="СОЛНЦЕ"); p.moon(label="ЛУНА")

        # Маркер цели
        p.marker(
            ra=target_pos[0], dec=target_pos[1],
            label="[ ЦЕЛЬ ]",
            style={
                "marker": {"size": 85, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 3.5, "line_style": [1, [5, 5]]},
                "label": {"font_size": 26, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 55}
            }
        )

        temp_file = "zenith_v16.png"
        p.export(temp_file, transparent=True, padding=0.03)

        # ШАГ 3: СБОРКА И КАЛИБРОВКА (Ниже и крупнее)
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA")
        
        # УВЕЛИЧИВАЕМ ДИАМЕТР до 1400px (почти на всю ширину фона)
        sky_img = sky_img.resize((1400, 1400))
        
        # СМЕЩАЕМ НИЖЕ: Y = 650 (это примерно на 3-4 см ниже прошлого варианта)
        # Центровка по X: (1440 - 1400) / 2 = 20
        bg_img.paste(sky_img, (20, 650), sky_img)

        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        # Текст (22px калибровка)
        t_col = '#D4E6FF'
        fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_final_v16.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0); plt.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        return True, path, target_name_rus, ""

    except Exception as e:
        return False, str(e), "", ""
