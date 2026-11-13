"""
Convierte el arte PNG a WebP para la app web (10x mas liviano: 135 MB -> 13 MB).

Los PNG masters quedan intactos para imprenta; la app (index.html y tiles_metadata.json)
apunta a las versiones .webp que genera este script.

Uso:  python tools/convertir-webp.py
"""
import os
import glob
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta Pillow. Instalalo con:  pip install pillow")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALIDAD = 86

total_png = total_webp = 0
for sub in ('Tiles', 'Cartas'):
    carpeta = os.path.join(BASE, 'imagenes', sub)
    for png in sorted(glob.glob(os.path.join(carpeta, '*.png'))):
        webp = png[:-4] + '.webp'
        Image.open(png).convert('RGB').save(webp, 'WEBP', quality=CALIDAD, method=6)
        a, b = os.path.getsize(png), os.path.getsize(webp)
        total_png += a
        total_webp += b
        print('%-36s %6.2f MB -> %5.2f MB' % (os.path.basename(png), a / 1048576, b / 1048576))

print('TOTAL %.1f MB -> %.1f MB' % (total_png / 1048576, total_webp / 1048576))
print('Despues hay que subir los .webp modificados:  git add -A && git commit -m "chore: regenerar arte web" && git push')
