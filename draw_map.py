import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime
import os, json, random
from PIL import Image
import ephem

# --- ЛИНГВИСТИЧЕСКИЙ МОДУЛЬ (РУССКИЙ ЯЗЫК) ---
RU_NAMES = {
    # Созвездия
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
    "Tucana": "Тукан", "Ursa Major": "Большая Медведица", "Ursa Minor": "Малая Медведица",
    "Vela": "Паруса", "Virgo": "Дева", "Volans": "Летучая Рыба", "Vulpecula": "Лисичка",
    # Яркие Звезды
    "Polaris": "Полярис", "Sirius": "Сириус", "Vega": "Вега", "Betelgeuse": "Бетельгейзе",
    "Rigel": "Ригель", "Arcturus": "Арктур", "Capella": "Капелла", "Altair": "Альтаир",
    "Aldebaran": "Альдебаран", "Antares": "Антарес", "Spica": "Спика", "Pollux": "Поллукс",
    "Castor": "Кастор", "Deneb": "Денеб", "Procyon": "Процион", "Regulus": "Регул",
    "Fomalhaut": "Фомальгаут", "Castor": "Кастор", "Pollux": "Поллукс",
    # Планеты и Метки
    "СОЛНЦЕ": "СОЛНЦЕ", "ЛУНА": "ЛУНА",
    "ЦЕЛЬ": "ЦЕЛЬ", "[ ЦЕЛЬ ]": "[ ЦЕЛЬ ]"
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
        "star": {"label": {"font_size": 13}},
        "constellation": {"label": {"font_size": 18, "font_weight": "bold"}},
        "planet": {"label": {"font_size": 18}}
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

    p = ZenithPlot(observer=observer, style=ZENITH_STYLE, resolution=2600, autoscale=True)

    # 1. Слой Горизонта, Млечного пути и Эклиптики
    p.horizon()
    p.milky_way()
    p.ecliptic()

    # 2. Слой Звезд и Метки
    # Отрисовываем созвездия, используя словарь для перевода на русский
    def translate_label(label):
        return RU_NAMES.get(label, label)

    p.stars(where=[_.magnitude < 6.0], where_labels=[_.magnitude < 2.5])
    
    # Применяем переводы к меткам на карте
    for label in p.ax.get_children():
        if isinstance(label, matplotlib.text.Text):
            text = label.get_text()
            if text in RU_NAMES:
                label.set_text(RU_NAMES[text])

    # 3. Созвездия и Планеты
    p.constellations()
    p.planets()
    p.sun(label="СОЛНЦЕ")
    p.moon(label="ЛУНА")

    # 4. МАРКЕР ЦЕЛИ
    p.marker(
        ra=target_pos[0], dec=target_pos[1],
        label="[ ЦЕЛЬ ]",
        style={
            "marker": {"size": 95, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 4, "line_style": [1, [6, 6]]},
            "label": {"font_size": 28, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 60}
        }
    )

    temp_file = "zenith_calibrated.png"
    p.export(temp_file, transparent=True, padding=0.1)

    # === СБОРКА И ЦЕНТРОВКА ===
    bg_img = Image.open('background1.png')
    sky_img = Image.open(temp_file).convert("RGBA")
    
    # КАЛИБРОВКА: Увеличиваем диаметр круга
    sky_img = sky_img.resize((1300, 1300))
    
    # КАЛИБРОВКА: Смещаем круг ниже (x, y)
    # y = 500 смещает круг на ~3 см (140px) ниже, чем в image_1.png
    bg_img.paste(sky_img, (200, 500), sky_img)

    # КАЛИБРОВКА: Увеличиваем figure canvas, чтобы вместить данные в рамках
    dpi = 100
    fig = plt.figure(figsize=(12, 19), dpi=dpi)
    ax_bg = fig.add_axes([0, 0, 1, 1])
    ax_bg.imshow(bg_img)
    ax_bg.axis('off')

    # Расчет данных для информационных рамок
    e_obs = ephem.Observer()
    e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), dt
    moon, sun = ephem.Moon(), ephem.Sun()
    moon.compute(e_obs); sun.compute(e_obs)
    rise = ephem.localtime(e_obs.next_rising(sun)).strftime('%H:%M')
    sset = ephem.localtime(e_obs.next_setting(sun)).strftime('%H:%M')

    # КАЛИБРОВКА: Текст данных (22px) переведен на русский и смещен под новые рамки
    t_col = '#D4E6FF'
    fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=22, fontweight='bold')
    fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=22, fontweight='bold')
    fig.text(0.38, 0.106, f"Фаза: {int(moon.phase)}%", color=t_col, fontsize=22, fontweight='bold')
    fig.text(0.40, 0.067, rise, color=t_col, fontsize=22, fontweight='bold')
    fig.text(0.74, 0.067, sset, color=t_col, fontsize=22, fontweight='bold')
    # fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold')

    path = f"sky_final_fixed.png"
    plt.savefig(path, bbox_inches='tight', pad_inches=0)
    plt.close()
    if os.path.exists(temp_file):
        os.remove(temp_file)
    return True, path, target_name_rus, ""
