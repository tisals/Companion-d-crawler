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
import json
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

    def num_obligatorio(v, donde):
        # Una formula sin valor en cache (el Excel se guardo con openpyxl y no se
        # recalculo) llega como None. Abortar es mejor que escribir 0 en el catalogo.
        if v is None:
            sys.exit(
                "ERROR: '%s' no tiene valor calculado (vacio o sin cache de la formula).\n"
                "       Abri el Excel, dejalo recalcular y guardalo (Ctrl+S) antes de sincronizar." % donde
            )
        try:
            return int(round(float(v)))
        except (TypeError, ValueError):
            sys.exit("ERROR: '%s' no es un numero: %r" % (donde, v))

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
            "energia": num_obligatorio(col(r, "Energía"), "Energía de " + nombre),
            "mueve": num_obligatorio(col(r, "Mueve"), "Mueve de " + nombre),
            "vida": num_obligatorio(col(r, "Vida (C/U)"), "Vida de " + nombre),
            "pd": num_obligatorio(col(r, "Puntos Despliegue"), "Puntos Despliegue de " + nombre),
            "ataque": num_obligatorio(col(r, "Ataque"), "Ataque de " + nombre),
            "dmgMin": num_obligatorio(col(r, "Daño min"), "Daño min de " + nombre),
            "dmgMax": num_obligatorio(col(r, "Daño max"), "Daño max de " + nombre),
            "tipoAtaque": txt(col(r, "Tipo ataque")),
            "modAtaque": txt(col(r, "Modificador Ataque")),
            "defensa": num(col(r, "Defensa")),
            "modDefensa": txt(col(r, "Modificador Defensa")),
            "califDefensa": num(col(r, "Calif Defensa")),
            "efecto": txt(col(r, "Efecto / Acción Especial")),
            "costoEnergia": num(col(r, "Costo Energía")),
        }
    # --- hoja 'otras': misiones y eventos ---
    otras = []
    if "otras" in wb.sheetnames:
        ws2 = wb["otras"]
        for row in ws2.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None:
                continue
            tipo = str(row[0]).strip()
            if tipo not in ("mision", "Evento"):
                continue
            try:
                num = int(row[1])
            except (TypeError, ValueError):
                continue
            otras.append({
                "tipo": tipo,
                "num": num,
                "copias": int(row[2]) if row[2] is not None else 1,
                "texto": str(row[3]).strip() if row[3] is not None else "",
            })
    return datos, otras


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


def generar_bloque_eventos(html, otras):
    """Escribe GAME_MISSIONS y GAME_EVENTS en index.html (hoja 'otras' del Excel)."""
    misiones = [o for o in otras if o["tipo"] == "mision"]
    eventos = [o for o in otras if o["tipo"] == "Evento"]

    def js(texto):
        # json.dumps produce un literal de cadena valido para JS (escapa saltos de
        # linea, comillas y barras) y se puede usar entre comillas simples.
        return json.dumps(texto, ensure_ascii=False)

    lineas_m = []
    for m in sorted(misiones, key=lambda x: x["num"]):
        lineas_m.append("            { num: %d, texto: %s }," % (m["num"], js(m["texto"])))

    lineas_e = []
    for e in sorted(eventos, key=lambda x: x["num"]):
        texto = e["texto"]
        enemigo = None
        efecto = None
        if "roba otra carta de evento" in texto:
            efecto = "roba"
        elif "retroceder 2 casillas" in texto:
            efecto = "retroceder"
        elif "no puedes moverte" in texto:
            efecto = "agotamiento"
        elif "Todos los enemigos se activan" in texto:
            efecto = "activar-todos"
        # Enemigo al que se refiere el evento ("Activa a X si esta en el tablero")
        if texto.startswith("Activa a "):
            resto = texto[len("Activa a "):]
            for sep in (" si ", ":"):
                if sep in resto:
                    resto = resto.split(sep, 1)[0]
                    break
            enemigo = ALIAS.get(resto.strip(), resto.strip())
        lineas_e.append("            { num: %d, copias: %d, texto: %s%s%s }," % (
            e["num"], e["copias"], js(texto),
            (", enemigo: %s" % js(enemigo)) if enemigo else "",
            (", efecto: %s" % js(efecto)) if efecto else ""))

    bloque = (
        "        // <<<SYNC-EVENTOS>>>\n"
        "        // MISIONES Y EVENTOS - fuente de verdad: hoja 'otras' del Excel\n"
        "        // Generado por tools/sync-enemigos.py - no editar a mano\n"
        "        const GAME_MISSIONS = [\n" + "\n".join(lineas_m) + "\n        ];\n\n"
        "        const GAME_EVENTS = [\n" + "\n".join(lineas_e) + "\n        ];\n"
        "        // <<<FIN-SYNC-EVENTOS>>>"
    )

    if "<<<SYNC-EVENTOS>>>" in html:
        # OJO: con lambda, porque re.sub interpretaria los \n del reemplazo.
        html = re.sub(r"        // <<<SYNC-EVENTOS>>>.*?// <<<FIN-SYNC-EVENTOS>>>",
                      lambda m: bloque, html, flags=re.S)
    else:
        # reemplaza el bloque MASTER_EVENTS heredado
        html = re.sub(r"        const MASTER_EVENTS = \[.*?\n        \];",
                      lambda m: bloque, html, flags=re.S)
    return html


def main():
    tmp = copiar_excel(os.path.join(tempfile.gettempdir(), "kikin_excel_sync.xlsx"))
    excel, otras = leer_excel(tmp)

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

    # --- misiones y eventos (hoja 'otras') ---
    html2 = generar_bloque_eventos(html2, otras)

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
