# Kikin Battles - Companion Táctico & Dungeon Master Hub

## Arquitectura del Proyecto

- **Paradigma**: Local-First & Mobile-First Single-Page Application (PWA).
- **Core Entry Point**: `index.html` en la raíz.
- **PWA Assets**: `manifest.json` y `sw.js` (Service Worker offline-first).
- **Almacenamiento**: `localStorage` reactivo (`kikin_battles_hub_v4`) + Exportación / Importación en JSON.
- **Assets Locales**:
  - Cartas de Héroes y Enemigos: `./imagenes/Cartas/*.png`
  - Tiles y losetas: `./imagenes/Tiles/*.png`

## Convenciones de Juego de Mesa

1. **Escala de Grilla**:
   - Casilla estándar: representa una loseta de 8x8 (pasillo, giro L, cruce T).
   - Sala Plegable: representa una pieza de 16x16 (ocupa 2x2 casillas en la grilla física y lógica).
   - Sin espacios en blanco (`gap: 0`): los tiles se conectan visualmente ocupando el 100% de la celda.
2. **Rotación de Tiles**:
   - Cada tile y sala puede rotarse en incrementos de 90° (`0°`, `90°`, `180°`, `270°`) para alinear puertas y entradas con el resto de la mazmorra.
3. **Tokens Superpuestos (1 a 4 por Tile)**:
   - 👾 **Enemigo** (amenaza presente en la sala).
   - ⚠️ **Trampa** (resorte oculto o mecanismo activo).
   - 💰 **Tesoro** (cofre o botín disponible).
   - 💎 **Mobiliario / Gema** (altar, biblioteca, mesa de pociones).
4. **Reglas de Entidades**:
   - **Héroes oficiales**: Inmutables y fijos (Robotex, Astro, Bicis, Gemelos, Nucis, Huggy). No se pueden borrar ni editar sus stats base.
   - **Enemigos y Mascotas**: Totalmente editables y parametrizables por campaña.
5. **Protocolo de Apertura de Sala**:
   - Integrado directamente en la vista de Mesa.
   - Flujo por tiempos: Revelar -> Sala en tensión -> Decisión de acción (Buscar / Trampa D6 / Avanzar sin buscar).

