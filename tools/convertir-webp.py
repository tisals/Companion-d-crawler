"""Regenera los .webp solo de los PNG que cambiaron (mtime mas nuevo que el webp).

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

convertidos = 0
total_png = total_webp = 0
for sub in ('Tiles', 'Cartas'):
    carpeta = os.path.join(BASE, 'imagenes', sub)
    for png in sorted(glob.glob(os.path.join(carpeta, '*.png'))):
        webp = png[:-4] + '.webp'
        if os.path.exists(webp) and os.path.getmtime(webp) >= os.path.getmtime(png):
            continue  # el webp ya esta al dia
        Image.open(png).convert('RGB').save(webp, 'WEBP', quality=CALIDAD, method=6)
        convertidos += 1
        print('regenerado: %s' % os.path.relpath(webp, BASE))
    for png in sorted(glob.glob(os.path.join(carpeta, '*.png'))):
        webp = png[:-4] + '.webp'
        if os.path.exists(webp):
            total_png += os.path.getsize(png)
            total_webp += os.path.getsize(webp)

print('')
print('webp regenerados: %d' % convertidos)
print('total arte web: %.1f MB (png masters: %.1f MB)' % (total_webp / 1048576, total_png / 1048576))
if convertidos:
    print('Despues:  git add -A && git commit -m "chore: regenerar arte web" && git push')
