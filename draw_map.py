import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random, gc
from PIL import Image, ImageDraw, ImageFont
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

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
    "leo": [152, 12], "virgo": [201, -11]
}

def generate_star_map(lat, lon, user_name):
    gc.collect()
    try:
        dt = datetime.now(timezone.utc)
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        target_key = random.choice(list(TARGETS.keys()))
        target_pos = TARGETS[target_key]
        target_name_rus = db.get(target_key, {}).get('name', target_key).split('(')[0].strip().upper()

        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        
        # Минималистичные шрифты для экономии RAM
        try:
            style.star.label.font_size = 10
            style.constellation.label.font_size = 18
            style.constellation.label.font_weight = 700
            style.constellation.line.stroke_width = 3.0
        except: pass

        # Resolution=900 — это "безопасная зона", чтобы Render не упал
        p = ZenithPlot(observer=observer, style=style, resolution=900, autoscale=True)
        p.horizon(); p.milky_way(); p.ecliptic(); p.constellations()

        # Русификация
        for text_obj in p.ax.texts:
            txt = text_obj.get_text()
            if txt in RU_NAMES: text_obj.set_text(RU_NAMES[txt])

        p.stars(where=[_.magnitude < 4.8], where_labels=[_.magnitude < 2.0])
        p.planets(); p.sun(label="СОЛНЦЕ"); p.moon(label="ЛУНА")

        p.marker(ra=target_pos[0], dec=target_pos[1], label="[ ЦЕЛЬ ]",
                style={"marker": {"size": 70, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 3},
                       "label": {"font_size": 22, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 50}})

        temp_file = "v24_tmp.png"
        p.export(temp_file, transparent=True, padding=0.01)
        plt.close('all')
        gc.collect()

        # === СБОРКА ЧЕРЕЗ PILLOW (ЛЕГКИЙ ВЕС) ===
        bg_img = Image.open('background1.png').convert("RGBA")
        sky_img = Image.open(temp_file).convert("RGBA")
        
        # Твои последние координаты из v23.0
        sky_size = 1750
        sky_img = sky_img.resize((sky_size, sky_size), Image.Resampling.LANCZOS)
        bg_img.paste(sky_img, (-350, 500), sky_img)
        
        # Рисуем текст прямо на картинке через ImageDraw (минус 150MB RAM по сравнению с plt)
        draw = ImageDraw.Draw(bg_img)
        # Если шрифта нет, PIL возьмет стандартный
        try:
            font = ImageFont.load_default(size=60)
        except:
            font = ImageFont.load_default()

        t_col = (212, 230, 255, 255) # Светло-голубой
        
        # Пишем данные в рамки (координаты подобраны под фон)
        draw.text((550, 2600), user_name.upper(), fill=t_col, font=font)
        draw.text((700, 2730), f"{float(lat):.2f}N, {float(lon):.2f}E", fill=t_col, font=font)
        draw.text((550, 3100), target_name_rus, fill=(255, 0, 255, 255), font=font)

        path = "sky_final_v24.png"
        bg_img.save(path, "PNG")
        
        # Очистка
        bg_img.close(); sky_img.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        gc.collect()
        
        return True, path, target_name_rus, ""

    except Exception as e:
        plt.close('all')
        gc.collect()
        return False, str(e), "", ""
