# Protocolo de prueba física + app (v1.1)

Objetivo: jugar una partida real con el tablero físico usando la app como herramienta
del DM, y que cada hallazgo quede **registrado con contexto** para convertirlo en
tareas concretas de la v1.1.

---

## 1. Antes de empezar la sesión

| Paso | Por qué |
|------|---------|
| Instalá la app en el celu desde <https://tisals.github.io/Companion-d-crawler/> | Es la versión que vamos a probar |
| Abrí **Ajustes & PWA → Eventos automáticos → APAGADOS** | Los eventos salen del mazo físico: si la app sortea los suyos, se contradicen |
| **Exportá el JSON** (Ajustes & PWA → 📥 Exportar JSON) y guardalo | Respaldo: si algo sale mal, la partida no se pierde |
| Anotá en un papel la fecha y la ambientación | Para identificar la sesión después |

La app ya trae las **5 misiones** (pestaña Bitácora) y el **mazo de 17 eventos**
(21 cartas: uno por enemigo + el genérico + los dos de Terror).

---

## 2. Qué verificar en cada momento de la partida

| Momento | Qué mirar | Qué anotar si falla |
|---------|-----------|--------------------|
| **Armado** | La ambientación (Caverna / Exterior) y que las salas 16x16 ocupen 2x2 | "¿Qué sala quedó mal pesada?" |
| **Entrada** | Que la puerta de la entrada apunte al lado correcto (el arte: línea roja = muro, punteada = salida) | Celda + lado esperado vs real |
| **Cada loseta revelada** | Las puertas del app vs el arte de la loseta | "¿La puerta N está donde no?" + celda |
| **Sala 16x16** | Los 8 segmentos (N1/N2/S1/S2/E1/E2/O1/O2) contra el arte | Segmento exacto (ej: "falta E2") |
| **Rotación de la sala** | Que al rotar la sala las puertas giren bien | Ángulo + puerta que quedó mal |
| **Enemigo que aparece** | La carta física contra la ficha del app: vida, atq (daño min-max), modificador de ataque, energía, movimiento, categoría, cantidad de copias | Enemigo + campo que difiere |
| **Combate** | El flujo de la ventana de combate: ¿alcanzás a todo rápido? ¿falta algún dato para tirar los dados? | Qué faltó y en qué momento |
| **Trampa / Tesoro / Mobiliario** | Las tablas de la app contra las cartas físicas | Tipo + valor |
| **Evento del mazo** | Sacá la carta del mazo físico y apretá **🎴** en esa misma carta de la app (o **🎴 Evento** en la Mesa para que sortee). ¿La regla se entiende? ¿Falta el enemigo a activar? | "El evento X no dice a quién activar" |
| **Misión / objetivo** | Marcá en **Bitácora → Misiones** la misión que está en curso y la que ya se hizo. ¿Sirve para llevar el objetivo? | "No sé cuál marcar" |
| **Fin de partida** | Si la Bitácora sirve como registro de lo que pasó | "¿Falta registrar X?" |
| **Entre partidas** | Exportar el JSON y pasarlo a las incidencias | — |

---

## 3. Cómo se anota

Corto y con ubicación. La app guarda el contexto sola (celda, tile, enemigo), así que
alcanza con:

> **Qué** pasó · **dónde** (celda 3,4 / sala / enemigo) · **qué esperabas** vs **qué pasó**

Ejemplos:
- "La puerta E de la Sala del Trono no aparece en el app, en la carta está abierta al este" → celda 2,3
- "La ficha de Drácula dice 32-44 en el app, la carta dice 26-32" → enemigo Drácula
- "Al rotar la sala al este, las puertas no giran"

---

## 4. Botón 🐞 Reportar

En la app:

- **En el modal de una celda** y **en la ficha de un enemigo**: botón **🐞 Reportar**.
  Se abre una caja de texto y se guarda la incidencia con el contexto automático
  (celda + tile, o enemigo + stats que muestra el app en ese momento).
- Todas las incidencias quedan listadas en **Ajustes & PWA → 🐞 Incidencias**.
- **Exportar incidencias** genera un archivo `.md` con la lista completa: se manda tal
  cual y de ahí salen las tareas de la v1.1.

Durante la partida: reportá y seguí jugando. No hace falta parar.

---

## 5. Qué NO mirar en esta sesión (para no distraerse)

Esto ya está decidido o es trabajo grande; anotalo si te aparece, pero no le des vueltas:

- **Categorías de las cartas**: Drácula y Nixar ya dicen "Jefe" en el app (en las cartas
  viejas decía "Principal"). Si re-imprimís cartas, fijate que coincidan.
- **Espectro**: el app dice Mueve 3 (Excel) y la carta dice 2. Anotá cuál usás.
- **Los dos eventos de Terror**: la app muestra la regla pero **no la aplica sola**
  (no hay posición de los héroes en el tablero): aplicála en la mesa y anotá si haría
  falta que la app la ejecute.
- **Misiones**: la app las muestra y las podés marcar, pero no las crea ni las valida
  contra el tablero. Si el objetivo necesita más (ej.: "encontrar el carro" → dónde
  va el carro), anotalo.

---

## 6. Después de la partida

1. En la app: **Ajustes & PWA → 🐞 Incidencias → Exportar** (`.md`).
2. **Exportá el JSON** de la partida y guardalo junto al `.md`.
3. Con esos dos archivos alcanza para armar la lista de la v1.1 sin volver a la mesa.
