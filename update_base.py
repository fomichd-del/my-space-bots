import json
import ephem
import os

# Обновленный словарь: Твой ключ в JSON -> Латинский код для ephem
mapping = {
    "andromeda": "And", "antlia": "Ant", "apus": "Aps", "aquarius": "Aqr",
    "aquila": "Aql", "ara": "Ara", "aries": "Ari", "auriga": "Aur",
    "bootes": "Boo", "caelum": "Cae", "camelopardalis": "Cam", "cancer": "Cnc",
    "canes_venatici": "CVn", "canis_major": "CMa", "canis_minor": "CMi", "capricornus": "Cap",
    "carina": "Car", "cassiopeia": "Cas", "centaurus": "Cen", "cepheus": "Cep",
    "cetus": "Cet", "chamaeleon": "Cha", "circinus": "Cir", "columba": "Col",
    "coma_berenices": "Com", "corona_australis": "CrA", "corona_borealis": "CrB", "corvus": "Crv",
    "crater": "Crt", "crux": "Cru", "cygnus": "Cyg", "delphinus": "Del",
    "dorado": "Dor", "draco": "Dra", "equuleus": "Equ", "eridanus": "Eri",
    "fornax": "For", "gemini": "Gem", "grus": "Gru", "hercules": "Her",
    "horologium": "Hor", "hydra": "Hya", "hydrus": "Hyi", "indus": "Ind",
    "lacerta": "Lac", "leo": "Leo", "leo_minor": "LMi", "lepus": "Lep",
    "libra": "Lib", "lupus": "Lup", "lynx": "Lyn", "lyra": "Lyr",
    "mensa": "Men", "microscopium": "Mic", "monoceros": "Mon", "musca": "Mus",
    "norma": "Nor", "octans": "Oct", "ophiuchus": "Oph", "orion": "Ori",
    "pavo": "Pav", "pegasus": "Peg", "perseus": "Per", "phoenix": "Phe",
    "pictor": "Pic", "pisces": "Psc", "piscis_austrinus": "PsA", "puppis": "Pup",
    "pyxis": "Pyx", "reticulum": "Ret", "sagitta": "Sge", "sagittarius": "Sgr",
    "scorpius": "Sco", "sculptor": "Scl", "scutum": "Sct", "serpens": "Ser",
    "sextans": "Sex", "taurus": "Tau", "telescopium": "Tel", "triangulum": "Tri",
    "triangulum_australe": "TrA", "tucana": "Tuc", "ursa_major": "UMa", "ursa_minor": "UMi",
    "vela": "Vel", "virgo": "Vir", "volans": "Vol", "vulpecula": "Vul"
}

def update_json():
    filename = 'constellations.json'
    if not os.path.exists(filename):
        return

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated_count = 0
    for key, info in data.items():
        iau_code = mapping.get(key.lower())
        if iau_code:
            info['id'] = iau_code
            updated_count += 1
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ Обновлено: {updated_count} из {len(data)}")

if __name__ == "__main__":
    update_json()
