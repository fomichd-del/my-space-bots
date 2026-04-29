import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random, gc
from PIL import Image
import ephem
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# --- ГЛОБАЛЬНЫЙ РУСИФИКАТОР ---
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
    "Vega": "Вега", "Polaris": "Полярис", "Sirius": "Сириус", "Arcturus": "Арктур", "Capella": "Капелла",
    "Sun": "СОЛНЦЕ", "Moon": "ЛУНА", "Mercury": "МЕРКУРИЙ", "Venus": "ВЕНЕРА", 
    "Mars": "МАРС", "Jupiter": "ЮПИТЕР", "Saturn": "САТУРН", "Uranus": "УРАН", "Neptune": "НЕПТУН"
}

# --- РАСШИРЕННАЯ БАЗА ЦЕЛЕЙ (30 шт) ---
TARGETS = {
    "ursa_major": [165, 56], "ursa_minor": [37, 89], "orion": [84, -5],
    "cassiopeia": [10, 59], "cygnus": [310, 45], "lyra": [279, 39],
    "aries": [31, 23], "taurus": [69, 16], "gemini": [114, 28],
    "cancer": [130, 20], "leo": [152, 12], "virgo": [201, -11],
    "libra": [226, -15], "scorpius": [250, -30], "sagittarius": [285, -25],
    "capricornus": [315, -20], "aquarius": [335, -10], "pisces": [15, 15],
    "andromeda": [15, 40], "aquila": [295, 3], "bootes": [220, 30],
    "canis_major": [100, -20], "centaurus": [195, -50], "cepheus": [330, 70],
    "draco": [260, 65], "hercules": [250, 30], "pegasus": [340, 20],
    "perseus": [50, 45], "auriga": [85, 42], "cetus": [25, -10]
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
        target_name_rus = RU_NAMES.get(target_key.replace('_', ' ').title(), target_key.upper())

        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        try:
            style.star.label.font_size = 12
            style.constellation.label.font_size = 14
            style.constellation.label.font_weight = 700
        except: pass

        p = ZenithPlot(observer=observer, style=style, resolution=1400, autoscale=True)

        p.horizon(); p.milky_way(); p.ecliptic(); p.constellations()

        # Аккуратный перевод
        for text_obj in p.ax.texts:
            txt = text_obj.get_text().replace('\n', ' ').title()
            for eng, rus in RU_NAMES.items():
                if eng in txt:
                    text_obj.set_text(text_obj.get_text().replace(eng, rus).replace(eng.upper(), rus))

        p.stars(where=[_.magnitude < 5.3], where_labels=[_.magnitude < 2.5])
        
        # Добавляем планеты, Солнце и Луну
        p.planets()
        p.sun()
        p.moon()

        # ЯРКАЯ И ЗАМЕТНАЯ ЦЕЛЬ (Неон)
        p.marker(
            ra=target_pos[0], dec=target_pos[1],
            label="[ 🎯 ЦЕЛЬ ВЫДЕЛЕНА ]",
            style={
                "marker": {"size": 200, "symbol": "circle", "fill": "none", "edge_color": "#00FFFF", "edge_width": 4},
                "label": {"font_size": 22, "font_weight": 800, "font_color": "#00FFFF", "offset_y": 55}
            }
        )

        temp_file = "v30_tmp.png"
        p.export(temp_file, transparent=True, padding=0.01)
        plt.close('all')

        # --- РАСЧЕТ ДЛЯ ПАНЕЛИ ---
        e_obs = ephem.Observer()
        e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), datetime.now()
        moon = ephem.Moon()
        moon.compute(e_obs)
        moon_phase = int(moon.phase)
        sun = ephem.Sun()
        sun.compute(e_obs)
        try:
            rise_time = ephem.localtime(e_obs.next_rising(sun)).strftime('%H:%M')
            set_time = ephem.localtime(e_obs.next_setting(sun)).strftime('%H:%M')
        except:
            rise_time, set_time = "--:--", "--:--"

        # === ФИНАЛЬНАЯ СБОРКА ===
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA")
        
        # УВЕЛИЧЕН ДИАМЕТР НА 2ММ (+20px). Идеальный размер для колец.
        sky_size = 900
        sky_img = sky_img.resize((sky_size, sky_size), Image.Resampling.LANCZOS)
        
        # Автоматическая центровка по горизонтали, корректировка по вертикали
        x_offset = (bg_img.width - sky_size) // 2
        y_offset = 360 
        bg_img.paste(sky_img, (x_offset, y_offset), sky_img)
        
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        t_col = '#D4E6FF'
        fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"{moon_phase}%", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise_time, color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, set_time, color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#00FFFF', fontsize=22, fontweight='bold')

        path = f"sky_final_v30.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=dpi)
        
        plt.close('all')
        bg_img.close(); sky_img.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        gc.collect()
        
        return True, path, target_name_rus, ""

    except Exception as e:
        plt.close('all')
        gc.collect()
        return False, str(e), "", ""
