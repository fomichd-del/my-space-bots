import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime
import os, json, random
from PIL import Image
import ephem

# --- ГЛОБАЛЬНЫЙ РУСИФИКАТОР (88 СОЗВЕЗДИЙ) ---
RU_NAMES = {
    "Andromeda": "Андромеда", "Antlia": "Насос", "Apus": "Райская Птица", "Aquarius": "Водолей",
    "Aquila": "Орел", "Ara": "Жертвенник", "Aries": "Овен", "Auriga": "Возничий", "Boötes": "Волопас",
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
    "Tucana": "Тукан", "Ursa Major": "Большая Медведица", "Ursa Minor": "Малый Медведица",
    "Vela": "Паруса", "Virgo": "Дева", "Volans": "Летучая Рыба", "Vulpecula": "Лисичка",
    "Vega": "Вега", "Polaris": "Полярис", "Sirius": "Сириус", "Arcturus": "Арктур", "Capella": "Капелла"
}

# --- КООРДИНАТЫ ЦЕЛЕЙ ---
TARGETS = {
    "ursa_major": [165, 56], "ursa_minor": [37, 89], "orion": [84, -5],
    "cassiopeia": [10, 59], "leo": [152, 12], "cygnus": [310, 45],
    "lyra": [279, 39], "gemini": [114, 28], "taurus": [69, 16],
    "aries": [31, 23], "pegasus": [345, 15]
}

# --- СТИЛЬ КАРТЫ (BLUE GOLD) ---
ZENITH_STYLE = PlotStyle().extend(
    extensions.BLUE_GOLD,
    extensions.GRADIENT_PRE_DAWN,
    {
        "star": {"label": {"font_size": 11, "font_weight": 500}},
        "constellation": {"label": {"font_size": 16, "font_weight": "bold"}, "line": {"stroke_width": 2.5}}
    }
)

def generate_star_map(lat, lon, user_name):
    dt = datetime.now()
    observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
    
    with open('constellations.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    target_key = random.choice(list(TARGETS.keys()))
    target_pos = TARGETS[target_key]
    target_name_rus = db[target_key]['name'].split('(')[0].strip().upper()

    # Отрисовка карты (увеличиваем resolution для Pillow resize)
    p = ZenithPlot(observer=observer, style=ZENITH_STYLE, resolution=2000, autoscale=True)

    # 1. Слой Горизонта, Млечного пути и Эклиптики
    p.horizon()
    p.milky_way()
    p.ecliptic()

    # 2. Слой Созвездий и Русификация (Глубокий Русификатор 11.0)
    p.constellations()
    
    # ПРИНУДИТЕЛЬНЫЙ РУССКИЙ ЯЗЫК ДЛЯ СОЗВЕЗДИЙ
    for text_obj in p.ax.texts:
        txt = text_obj.get_text()
        if txt in RU_NAMES:
            text_obj.set_text(RU_NAMES[txt])

    # 3. Слой Звезд, Планет, Луны и Цели
    p.stars(where=[_.magnitude < 5.8], where_labels=[_.magnitude < 2.5])
    
    # Русификация ярких звезд (Вега, Сириус, Полярис)
    for text_obj in p.ax.texts:
        txt = text_obj.get_text()
        if txt in RU_NAMES:
            text_obj.set_text(RU_NAMES[txt])

    p.planets()
    p.sun(label="СОЛНЦЕ")
    p.moon(label="ЛУНА")

    # Маркер цели
    p.marker(
        ra=target_pos[0], dec=target_pos[1],
        label="[ ЦЕЛЬ ]",
        style={
            "marker": {"size": 85, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 3.5, "line_style": [1, [5, 5]]},
            "label": {"font_size": 26, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 55}
        }
    )

    temp_file = "zenith_calibrated.png"
    # Снижаем padding, чтобы W лучше попало на В
    p.export(temp_file, transparent=True, padding=0.03)

    # === СБОРКА И ЦЕНТРОВКА (Ювелирная калибровка 11.0) ===
    bg_img = Image.open('background1.png')
    sky_img = Image.open(temp_file).convert("RGBA")
    
    # Аналитическая стыковка: увеличиваем до 1300, чтобы скрыть фоновые кольца
    sky_img = sky_img.resize((1300, 1300))
    
    # Финальные координаты наложения: сдвиг вправо на 8 мм (+150px), вниз (+100px)
    # y = 360 смещает W точно поверх В
    bg_img.paste(sky_img, (60, 360), sky_img)

    # === ВОССТАНОВЛЕНИЕ ТЕКСТА В РАМКАХ (ImageDraw 11.0) ===
    # Отрисовываем данные через Matplotlib поверх bg_img
    dpi = 100
    fig = plt.figure(figsize=(12, 19), dpi=dpi)
    ax_bg = fig.add_axes([0, 0, 1, 1])
    ax_bg.imshow(bg_img)
    ax_bg.axis('off')

    # Расчет данных (Луна, Солнце)
    e_obs = ephem.Observer()
    e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), dt
    moon = ephem.Moon()
    moon.compute(e_obs)
    
    sun = ephem.Sun()
    sun.compute(e_obs)
    rise = ephem.localtime(e_obs.next_rising(sun)).strftime('%H:%M')
    sset = ephem.localtime(e_obs.next_setting(sun)).strftime('%H:%M')

    # Добавление текста в рамки. Координаты аналитически пересчитаны.
    t_col = '#D4E6FF' # Светло-голубой
    # fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=22, fontweight='bold') # Пилот
    # fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=22, fontweight='bold') # Коорд
    fig.text(0.38, 0.106, f"Фаза: {int(moon.phase)}%", color=t_col, fontsize=22, fontweight='bold') # Луна
    fig.text(0.40, 0.067, rise, color=t_col, fontsize=22, fontweight='bold') # Восход
    fig.text(0.74, 0.067, sset, color=t_col, fontsize=22, fontweight='bold') # Закат
    fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold') # Цель

    path = f"sky_final_fixed.png"
    plt.savefig(path, bbox_inches='tight', pad_inches=0)
    plt.close()

    if os.path.exists(temp_file):
        os.remove(temp_file)

    return True, path, target_name_rus, ""
