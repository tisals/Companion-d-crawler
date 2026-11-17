"""
Sincroniza el catalogo de enemigos de la app (index.html) con la hoja "Cartas"
del Excel "listado de cartas2.xlsx", que es la fuente de verdad de los datos.

Uso:
    python tools/sync-enemigos.py

Que hace:
  - Copia el Excel a una carpeta temporal (si esta abierto en Excel, el archivo
    esta bloqueado y no se puede leer directamente).
  - Reescribe DEFAULT_CUSTOM_ENTITIES con los datos del Excel.
  - Refresca LEGACY_DEFAULT_STATS con los valores que estaban desplegados (HEAD),
    para que la migracion actualice las fichas intactas y respete las editadas
    a mano.
  - Verifica al final que el bloque resultante coincide con el Excel.

El Excel manda en los DATOS (vida, ataque, dano, modificadores, categoria, efecto).
Los textos de efecto se corrigen de unas erratas conocidas al importarlos; si
preferis el texto tal cual del Excel, sacalas de la lista NORMALIZACIONES.
"""
import os
import glob
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(BASE, "index.html")
EXCEL = os.path.join(BASE, "listado de cartas2.xlsx")

# Erratas del Excel que se corrigen al importar (el resto se toma textual).
NORMALIZACIONES = [
    ("sus Ataques no", "sus ataques no"),
    ("sus taque no", "sus ataques no"),
    ("5-6:-5", "5-6: -5"),
    ("Vortice:", "Vórtice:"),
    ("en area ", "en área "),
]

# Nombre en la app -> nombre en el Excel
ALIAS = {"Dragón": "Cria Dragón", "Huggy Kissy": "Huggy-Kissy"}

CAMPOS = ("cost", "stats", "img", "locked", "category", "copies", "energy", "move",
          "attack", "dmgMin", "dmgMax", "attackType", "energyCost", "atkMod",
          "defMod", "defRating", "effect")


def normalizar(texto):
    for viejo, nuevo in NORMALIZACIONES:
        texto = texto.replace(viejo, nuevo)
    return texto


def copiar_excel(destino):
    """El Excel abierto en Excel bloquea el archivo: se copia a una carpeta temporal."""
    if not os.path.exists(EXCEL):
        sys.exit("No se encuentra el Excel: %s" % EXCEL)
    try:
        shutil.copyfile(EXCEL, destino)
        return destino
    except PermissionError:
        tmp = os.path.join(tempfile.gettempdir(), "kikin_excel_%d.xlsx" % os.getpid())
        shutil.copyfile(EXCEL, tmp)
        print("El Excel esta abierto: se leyo una copia temporal.")
        return tmp


def leer_excel(ruta):
    try:
        import openpyxl
    except ImportError:
        sys.exit("Falta openpyxl. Instalalo con:  pip install openpyxl")
    wb = openpyxl.load_workbook(ruta, data_only=True)
    ws = wb["Cartas"]
    rows = [[("" if v is None else v) for v in r] for r in ws.iter_rows(values_only=True)]
    head = [str(h).strip() for h in rows[0]]

    def col(row, name):
        i = head.index(name)
        return row[i] if i < len(row) else ""

    def num(v, default=0):
        try:
            return int(round(float(v)))
        except (TypeError, ValueError):
            return default

    def txt(v):
        return str(v).strip() if v is not None else ""

    datos = {}
    for r in rows[1:]:
        nombre = txt(col(r, "Nombre"))
        if not nombre or txt(col(r, "Tipo")) != "Enemigo":
            continue
        datos[nombre] = {
            "cantidad": num(col(r, "Cantidad"), 1),
            "categoria": txt(col(r, "Categoría")),
            "energia": num(col(r, "Energía")),
            "mueve": num(col(r, "Mueve")),
            "vida": num(col(r, "Vida (C/U)")),
            "pd": num(col(r, "Puntos Despliegue")),
            "ataque": num(col(r, "Ataque")),
            "dmgMin": num(col(r, "Daño min")),
            "dmgMax": num(col(r, "Daño max")),
            "tipoAtaque": txt(col(r, "Tipo ataque")),
            "modAtaque": txt(col(r, "Modificador Ataque")),
            "defensa": num(col(r, "Defensa")),
            "modDefensa": txt(col(r, "Modificador Defensa")),
            "califDefensa": num(col(r, "Calif Defensa")),
            "efecto": txt(col(r, "Efecto / Acción Especial")),
            "costoEnergia": num(col(r, "Costo Energía")),
        }
    return datos


def parse_entidades(texto):
    """Extrae cada objeto { type: ..., ... } del bloque, tolerando el formato."""
    out = []
    for m in re.finditer(r"\{\s*type: '([^']+)',\s*name: '([^']+)'(.*?)\}", texto, re.S):
        cuerpo = m.group(3)
        e = {"type": m.group(1), "name": m.group(2)}
        for campo in CAMPOS:
            cm = re.search(campo + r":\s*('(?:[^'\\]|\\.)*'|[^,\n]+)", cuerpo)
            if cm:
                v = cm.group(1).strip()
                if v.startswith("'") and v.endswith("'"):
                    v = v[1:-1].replace("\\'", "'")
                e[campo] = v
        out.append(e)
    return out


def render(ents):
    lineas = []
    for e in ents:
        lineas.append(
            "            { type: '%s', name: '%s', cost: %s, stats: '%s', img: '%s', locked: %s,\n"
            "              category: '%s', copies: %d, energy: %d, move: %d, attack: %d, dmgMin: %d, dmgMax: %d, attackType: '%s', energyCost: %d,\n"
            "              atkMod: '%s', defMod: '%s', defRating: %d,\n"
            "              effect: '%s' }" % (
                e["type"], e["name"], e["cost"], e["stats"], e["img"], e.get("locked", "false"),
                e["category"], int(e["copies"]), int(e["energy"]), int(e["move"]), int(e["attack"]),
                int(e["dmgMin"]), int(e["dmgMax"]), e["attackType"], int(e["energyCost"]),
                e["atkMod"], e["defMod"], int(e["defRating"]), e["effect"].replace("'", "\\'")))
    return ",\n".join(lineas)


def main():
    tmp = copiar_excel(os.path.join(tempfile.gettempdir(), "kikin_excel_sync.xlsx"))
    excel = leer_excel(tmp)

    excel_por_app = {}
    for ex_name, ex in excel.items():
        app_name = next((a for a, e in ALIAS.items() if e == ex_name), ex_name)
        excel_por_app[app_name] = ex

    html = open(HTML, encoding="utf-8").read()
    bloque = re.search(r"const DEFAULT_CUSTOM_ENTITIES = \[(.*?)\n        \];", html, re.S).group(1)
    entidades = parse_entidades(bloque)
    print("entradas en el codigo: %d | enemigos en el Excel: %d" % (len(entidades), len(excel)))

    nuevas = []
    for e in entidades:
        ex = excel_por_app.get(e["name"])
        if not ex:
            print("  sin equivalente en Excel (se deja como esta):", e["name"])
            nuevas.append(e)
            continue
        nuevo = dict(e)
        nuevo.update({
            "cost": str(ex["pd"]),
            "stats": "Vida: %d | Atq: %d-%d | Def: %d" % (ex["vida"], ex["dmgMin"], ex["dmgMax"], ex["defensa"]),
            "category": ex["categoria"],
            "copies": ex["cantidad"],
            "energy": ex["energia"],
            "move": ex["mueve"],
            "attack": ex["ataque"],
            "dmgMin": ex["dmgMin"],
            "dmgMax": ex["dmgMax"],
            "attackType": ex["tipoAtaque"],
            "energyCost": ex["costoEnergia"],
            "atkMod": ex["modAtaque"] or "—",
            "defMod": normalizar(ex["modDefensa"]) or "—",
            "defRating": ex["califDefensa"],
            "effect": normalizar(ex["efecto"]),
        })
        dif = [k for k in CAMPOS if k not in ("img", "locked") and str(e.get(k)) != str(nuevo[k])]
        if dif:
            print("* %s" % e["name"])
            for k in dif:
                print("     %-12s %r -> %r" % (k, e.get(k), nuevo[k]))
        nuevas.append(nuevo)

    nuevo_bloque = render(nuevas)
    html2 = re.sub(r"(const DEFAULT_CUSTOM_ENTITIES = \[\n)(.*?)(\n        \];)",
                   lambda m: m.group(1) + nuevo_bloque + m.group(3), html, flags=re.S)

    # LEGACY_DEFAULT_STATS = valores desplegados (HEAD) para detectar editions a mano
    head_html = subprocess.run(["git", "show", "HEAD:index.html"], cwd=BASE,
                               capture_output=True, text=True, encoding="utf-8").stdout
    head_bloque = re.search(r"const DEFAULT_CUSTOM_ENTITIES = \[(.*?)\n        \];", head_html, re.S).group(1)
    head_stats = {e["name"]: e["stats"] for e in parse_entidades(head_bloque)}
    legacy = "        const LEGACY_DEFAULT_STATS = {\n"
    for e in entidades:
        if e["name"] in head_stats:
            legacy += "            '%s': '%s',\n" % (e["name"], head_stats[e["name"]])
    legacy += "        };"
    html2 = re.sub(r"        const LEGACY_DEFAULT_STATS = \{.*?\n        \};", legacy, html2, flags=re.S)

    open(HTML, "w", encoding="utf-8", newline="").write(html2)

    # verificacion
    h = open(HTML, encoding="utf-8").read()
    b = re.search(r"const DEFAULT_CUSTOM_ENTITIES = \[(.*?)\n        \];", h, re.S).group(1)
    fin = parse_entidades(b)
    problemas = []
    for e in fin:
        ex = excel_por_app.get(e["name"])
        if not ex:
            continue
        esperado = {
            "cost": str(ex["pd"]),
            "stats": "Vida: %d | Atq: %d-%d | Def: %d" % (ex["vida"], ex["dmgMin"], ex["dmgMax"], ex["defensa"]),
            "category": ex["categoria"], "copies": str(ex["cantidad"]), "energy": str(ex["energia"]),
            "move": str(ex["mueve"]), "attack": str(ex["ataque"]), "dmgMin": str(ex["dmgMin"]),
            "dmgMax": str(ex["dmgMax"]), "attackType": ex["tipoAtaque"],
            "energyCost": str(ex["costoEnergia"]), "atkMod": ex["modAtaque"] or "—",
            "defMod": normalizar(ex["modDefensa"]) or "—", "defRating": str(ex["califDefensa"]),
            "effect": normalizar(ex["efecto"]),
        }
        for k, v in esperado.items():
            if str(e.get(k)) != str(v):
                problemas.append((e["name"], k, e.get(k), v))
    print("")
    print("entradas tras el cambio: %d" % len(fin))
    print("campos que no coinciden con el Excel: %d" % len(problemas))
    for p in problemas[:12]:
        print("   ", p)
    if problemas:
        sys.exit("ERROR: el bloque no coincide con el Excel")
    print("Sincronizacion correcta.")


if __name__ == "__main__":
    main()
