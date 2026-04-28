import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random, gc
from PIL import Image
import warnings

# Глушим технические предупреждения
warnings.filterwarnings("ignore", category=FutureWarning)

# --- ГЛОБАЛЬНЫЙ РУСИФИКАТОР (88 СОЗВЕЗДИЙ) ---
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
    # Очистка памяти перед стартом
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
        
        # Настройка шрифтов (700 = Bold)
        try:
            style.star.label.font_size = 12
            style.star.label.font_weight = 500
            style.constellation.label.font_size = 20
            style.constellation.label.font_weight = 700
            style.constellation.line.stroke_width = 4.0
            style.planet.label.font_size = 18
            style.planet.label.font_weight = 700
        except: pass

        # resolution=1100 - ОПТИМИЗИРОВАНО ДЛЯ ПАМЯТИ (как в v20.0)
        p = ZenithPlot(observer=observer, style=style, resolution=1100, autoscale=True)

        p.horizon(); p.milky_way(); p.ecliptic(); p.constellations()

        # ПРИНУДИТЕЛЬНЫЙ РУССКИЙ ЯЗЫК
        # 1. Заменяем через API Starplot
        labels = p.constellation_labels()
        if labels:
            for l in labels:
                if l.text in RU_NAMES: l.text = RU_NAMES[l.text]
        
        # 2. Дублируем через прямой доступ к тексту Matplotlib
        for text_obj in p.ax.texts:
            txt = text_obj.get_text()
            if txt in RU_NAMES: text_obj.set_text(RU_NAMES[txt])

        p.stars(where=[_.magnitude < 5.3], where_labels=[_.magnitude < 2.3])
        p.planets(); p.sun(label="СОЛНЦЕ"); p.moon(label="ЛУНА")

        # Маркер цели
        p.marker(
            ra=target_pos[0], dec=target_pos[1],
            label="[ ЦЕЛЬ ]",
            style={
                "marker": {"size": 100, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 4, "line_style": [1, [5, 5]]},
                "label": {"font_size": 28, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 65}
            }
        )

        temp_file = "v21_tmp.png"
        p.export(temp_file, transparent=True, padding=0.01)
        
        # Закрываем фигуру Starplot, чтобы освободить RAM
        plt.close('all')

        # === СБОРКА И КОРРЕКЦИЯ: ВЛЕВО И ВВЕРХ (PIL) ===
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA")
        
        # Масштаб 1750px (перекрывает фоновые кольца)
        sky_size = 1750
        sky_img = sky_img.resize((sky_size, sky_size), Image.Resampling.LANCZOS)
        
        # НОВЫЕ КООРДИНАТЫ (ВЛЕВО И ВВЕРХ)
        # y_offset = 650 (сдвиг вверх на ~150 пикселей / 1.5 см от визуальной базы 800)
        # x_offset = -500 (сдвиг влево на ~150 пикселей / 1.5 см от визуальной базы -350)
        bg_img.paste(sky_img, (-500, 650), sky_img)
        
        # Финальный текст рисуем через Matplotlib на маленьком холсте (защита OOM)
        dpi = 80
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        # Информационные данные (22px)
        t_col = '#D4E6FF'
        fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_final_v21.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=dpi)
        
        # ТОТАЛЬНАЯ ОЧИСТКА
        plt.close('all')
        bg_img.close(); sky_img.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        gc.collect()
        
        return True, path, target_name_rus, ""

    except Exception as e:
        plt.close('all')
        gc.collect()
        return False, str(e), "", ""
