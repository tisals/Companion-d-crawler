# Publicar Kikin Battles en GitHub Pages (instalable desde el celu)

La app ya quedó preparada para instalarse: `manifest.json` con iconos reales (192 / 512 / maskable),
`sw.js` que precachea el shell para uso offline y el arte en WebP (135 MB → 13 MB, clave para datos móviles).

## Pasos (unos 3 minutos)

### 1. Crear el repositorio
En <https://github.com/new>:
- **Nombre**: `kikin-battles`
- **Visibilidad**: **Public** — GitHub Pages en cuentas gratuitas solo funciona en repositorios públicos.
- **No** tildes "Add a README" ni "Add a .gitignore": el repo local ya tiene commits.

### 2. Subir el código
```bash
cd "D:\OneDrive\Documentos personales\Documentos personales\entretenimiento Personal\juegos de Mesa\4. Interes\Kikin battles"
git remote add origin https://github.com/TU_USUARIO/kikin-battles.git
git push -u origin main
```
Git te abre el navegador para iniciar sesión (Git Credential Manager). No hace falta token manual.

### 3. Activar GitHub Pages
En el repo: **Settings → Pages → Build and deployment**
- Source: **Deploy from a branch**
- Branch: **main**, carpeta: **/ (root)** → **Save**

Tarda 1–2 minutos. Queda en `https://TU_USUARIO.github.io/kikin-battles/`.

### 4. Instalarlo en el celu
- **Android (Chrome)**: abrir la URL → menú ⋮ → **Instalar aplicación**.
- **iPhone (Safari)**: abrir la URL → botón Compartir → **Agregar a pantalla de inicio**.

Queda con icono propio (espadas cruzadas), se abre sin barras del navegador y **funciona sin internet**
(el service worker cachea el shell; las losetas que ya viste quedan cacheadas al uso).

## Cosas que conviene saber

- **Cada dispositivo tiene su propia partida**: el estado vive en el `localStorage` del navegador.
- **El repo NO lleva el material de imprenta**: los PDF de impresión, los PSD y los PNG masters (135 MB)
  siguen en esta carpeta de OneDrive; al repo solo van los `.webp` que usa la app.
- **Si cambiás una imagen**: volvé a exportarla como PNG y corré `python tools/convertir-webp.py`,
  después `git add -A && git commit && git push`.
- **Las puertas/entradadas** viven en `tiles_metadata.json`: se editan en la app y se Bajan con
  *Ajustes & PWA → Exportar JSON*; hay que copiar ese archivo al repo y volver a subirlo.
- Si abrís la app con doble clic (`file://`), el navegador bloquea la lectura del JSON por CORS y
  quedan las puertas del respaldo que está en `index.html`.
