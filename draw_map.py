import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random
from PIL import Image
import ephem

# --- ПОЛНЫЙ СЛОВАРЬ (88 СОЗВЕЗДИЙ + ЯРКИЕ ЗВЕЗДЫ) ---
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

TARGETS = {
    "ursa_major": [165, 56], "ursa_minor": [37, 89], "orion": [84, -5],
    "cassiopeia": [10, 59], "leo": [152, 12], "cygnus": [310, 45],
    "gemini": [114, 28], "taurus": [69, 16], "lyra": [279, 39],
    "andromeda": [10, 41], "pegasus": [345, 15]
}

def generate_star_map(lat, lon, user_name):
    try:
        dt = datetime.now(timezone.utc)
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        target_key = random.choice(list(TARGETS.keys()))
        target_pos = TARGETS[target_key]
        target_name_rus = db[target_key]['name'].split('(')[0].strip().upper()

        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        
        # Калибровка шрифтов
        try:
            style.star.label.font_size = 11
            style.constellation.label.font_size = 16
            style.constellation.line.stroke_width = 2.5
            style.planet.label.font_size = 14
        except: pass

        p = ZenithPlot(observer=observer, style=style, resolution=2400, autoscale=True)

        p.horizon()
        p.milky_way()
        p.ecliptic()
        
        # РИСУЕМ СОЗВЕЗДИЯ И ПЕРЕВОДИМ
        p.constellations()
        labels = p.constellation_labels()
        if labels:
            for l in labels:
                if l.text in RU_NAMES: l.text = RU_NAMES[l.text]

        # ЗВЕЗДЫ С ПЕРЕВОДОМ
        p.stars(where=[_.magnitude < 5.0], where_labels=[_.magnitude < 2.2])
        # (Опционально: ручной перевод меток звезд можно добавить тут, но пока оставим так)

        p.planets()
        p.sun(label="СОЛНЦЕ")
        p.moon(label="ЛУНА")

        # МАРКЕР ЦЕЛИ
        p.marker(
            ra=target_pos[0], dec=target_pos[1],
            label="[ ЦЕЛЬ ]",
            style={
                "marker": {"size": 80, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 3, "line_style": [1, [5, 5]]},
                "label": {"font_size": 24, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 50}
            }
        )

        temp_file = "zenith_calibrated.png"
        p.export(temp_file, transparent=True, padding=0)

        # === ТОЧНАЯ КАЛИБРОВКА НАЛОЖЕНИЯ ===
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA")
        
        # Уменьшаем размер неба, чтобы оно вписалось в кольцо
        sky_img = sky_img.resize((1020, 1020))
        
        # ЦЕНТРИРОВАНИЕ: (X=30, Y=660) - подобрано по твоему скриншоту
        bg_img.paste(sky_img, (30, 660), sky_img)

        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        # Расчет данных для текста
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

        path = f"sky_final_fixed.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0); plt.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        return True, path, target_name_rus, ""

    except Exception as e:
        return False, str(e), "", ""
