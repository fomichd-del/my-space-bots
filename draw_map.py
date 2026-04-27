import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random
from PIL import Image
import ephem

# --- ПОЛНЫЙ ГАЛАКТИЧЕСКИЙ СЛОВАРЬ (88 СОЗВЕЗДИЙ + ЗВЕЗДЫ) ---
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
    "Vega": "Вега", "Polaris": "Полярная", "Sirius": "Сириус", "Arcturus": "Арктур", "Capella": "Капелла", "Altair": "Альтаир"
}

# РАСШИРЕННАЯ БАЗА ЦЕЛЕЙ (88 созвездий + Зодиак + Звезды)
TARGETS = {
    "ursa_major": [165, 56], "ursa_minor": [37, 89], "orion": [84, -5],
    "cassiopeia": [10, 59], "cygnus": [310, 45], "lyra": [279, 39],
    "aquila": [297, 8], "pegasus": [345, 15], "andromeda": [10, 41],
    "perseus": [52, 49], "auriga": [79, 46], "bootes": [214, 19],
    "aries": [31, 23], "taurus": [69, 16], "gemini": [114, 28],
    "cancer": [130, 20], "leo": [152, 12], "virgo": [201, -11],
    "libra": [228, -15], "scorpius": [250, -35], "sagittarius": [286, -25],
    "capricornus": [315, -20], "aquarius": [335, -10], "pisces": [5, 15],
    "hercules": [250, 27], "draco": [255, 67], "sirius": [101.28, -16.71],
    "vega": [279.23, 38.78], "arcturus": [213.91, 19.18], "polaris": [37.95, 89.26]
}

def generate_star_map(lat, lon, user_name):
    try:
        # 1. Время с часовым поясом (Исправляет ошибку timezone_aware)
        dt = datetime.now(timezone.utc)
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        target_key = random.choice(list(TARGETS.keys()))
        target_pos = TARGETS[target_key]
        target_name_rus = db.get(target_key, {}).get('name', target_key).split('(')[0].strip().upper()

        # 2. Настройка стиля (Безопасно для Pydantic)
        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        
        # Ручная калибровка шрифтов (используем try, чтобы не падать)
        try:
            style.star.label.font_size = 12
            style.constellation.label.font_size = 18
            style.constellation.line.stroke_width = 3.0
            style.planet.label.font_size = 16
        except: pass

        p = ZenithPlot(observer=observer, style=style, resolution=2400, autoscale=True)

        # 3. Отрисовка слоев
        p.horizon()
        p.milky_way()
        p.ecliptic()
        p.constellations()

        # ПЕРЕВОД (88 созвездий)
        labels = p.constellation_labels()
        if labels is not None:
            for l in labels:
                if l.text in RU_NAMES: l.text = RU_NAMES[l.text]

        p.stars(where=[_.magnitude < 5.2], where_labels=[_.magnitude < 2.5])
        p.planets()
        p.sun(label="СОЛНЦЕ"); p.moon(label="ЛУНА")

        # 4. МАРКЕР ЦЕЛИ
        p.marker(
            ra=target_pos[0], dec=target_pos[1],
            label="[ ЦЕЛЬ ]",
            style={
                "marker": {"size": 95, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 4, "line_style": [1, [6, 6]]},
                "label": {"font_size": 28, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 60}
            }
        )

        temp_file = "final_zenith.png"
        p.export(temp_file, transparent=True, padding=0.05)

        # 5. СБОРКА И ЦЕНТРОВКА
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA")
        
        # Калибровка размера (увеличим чуть-чуть до 1040)
        sky_img = sky_img.resize((1040, 1040))
        
        # Координаты вставки (X, Y) - подправлено для центровки
        bg_img.paste(sky_img, (200, 360), sky_img)

        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        # РАСЧЕТ ДАННЫХ ДЛЯ ТЕКСТА (ephem)
        e_obs = ephem.Observer(); e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), dt.strftime('%Y/%m/%d %H:%M:%S')
        moon, sun = ephem.Moon(), ephem.Sun()
        moon.compute(e_obs); sun.compute(e_obs)
        
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

        path = f"sky_final_v14.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0); plt.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        return True, path, target_name_rus, ""

    except Exception as e:
        return False, str(e), "", ""
