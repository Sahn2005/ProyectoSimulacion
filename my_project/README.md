# Microrred solar de respaldo - Mapa real de Cienaga (Magdalena)

Simulacion en **Webots** del proyecto final: instalar paneles solares con
bateria de respaldo para contrarrestar los cortes de luz en Cienaga,
Magdalena. Todo se simula sobre el **mapa real** (levantamiento CAD) de la zona.

## Que se ve

- El **terreno real** importado desde `cad-atlas_3D.obj`.
- **31 edificios** generados desde las huellas de construccion del CAD, con
  ventanas en sus 4 fachadas:
  - **15 con panel solar** en el techo (+ bateria): siguen encendidos en
    **verde** durante el corte.
  - **16 sin panel solar**: se **apagan** por completo en cada corte.
- Una **torre de la red publica** en el centro del mapa, con una luz que
  parpadea en rojo durante los cortes.
- La **bandera de Cienaga** (dos franjas horizontales iguales: amarillo arriba,
  verde abajo) ondeando en un asta de 14 m en la plazoleta libre del centro del
  mapa, a la izquierda de la torre. Esta hecha de 16 franjas verticales que el
  controlador mueve en cada paso con una onda (se cambia la posicion en
  `FLAG_X`, `FLAG_Z`, `FLAG_Y` de `gen_world.py`; el movimiento se ajusta con
  `WAVE_AMP` y `WAVE_SPEED` en el controlador).
- Dos pantallas superpuestas (overlay) en la vista 3D:
  - **hud**: estado de la red, estado de cada grupo y barra de bateria.
  - **cronograma**: cronograma de 3 meses (12 semanas) en vivo, sincronizado con
    el reloj de la simulacion.

## Instalacion y uso

1. Instalar **Webots R2023b** (o compatible): https://cyberbotics.com/
2. Descomprimir el proyecto.
3. En Webots: `File > Open World...` -> `worlds/cienaga_microgrid.wbt`.
4. **Dar play (▶)** en la barra superior: Webots abre los mundos en pausa y el
   controlador solo corre mientras la simulacion avanza.
5. Mirar la **consola** (abajo): debe imprimir
   `[grid_supervisor] ventanas sin solar: 182, con solar: 206, torre: ok`.
   Si dice 0 ventanas o "NO ENCONTRADA", regenerar el mundo (`python3 gen_world.py`).

## Ajustes

En `controllers/grid_supervisor/grid_supervisor.py`:

| Constante | Que controla |
|---|---|
| `GRID_UP_DURATION` / `GRID_DOWN_DURATION` | Segundos con red activa / de corte |
| `BATTERY_DRAIN_PER_STEP` / `BATTERY_CHARGE_PER_STEP` | Velocidad de descarga / recarga |
| `CICLO_CRONOGRAMA_SEGUNDOS` | Segundos de simulacion que dura el cronograma completo |

En `gen_world.py` (luego correr `python3 gen_world.py`):

| Constante | Que controla |
|---|---|
| `COMPARAR_CON_Y_SIN_SOLAR` | `True`: mitad con panel y mitad sin (comparacion). `False`: todos los edificios que puedan llevar panel lo tienen |
| `ALTURA_EDIFICIO_REAL` | Altura generica de los edificios (el CAD no trae alturas) |
| `PANEL_W`, `PANEL_D` | Tamano de cada panel |

## Sobre el archivo CAD

- Contiene: malla de **terreno**, 33 curvas cerradas que son **huellas de
  construccion** y 3 curvas gigantes que son el **contorno del levantamiento**.
- **No** trae textura/foto ni etiquetas de calles, barrios o coordenadas, asi
  que no se puede confirmar por software a que cuadra exacta corresponde.
- Las curvas son datos NURBS que el importador de Webots no soporta; se
  quitaron del `.obj` (la copia limpia es la que usa el proyecto) y su
  posicion/tamano se reutilizo para generar los edificios. Los edificios son
  cajas de un piso: representacion aproximada, no modelo arquitectonico.
- Rhino usa Y hacia arriba y Webots Z: por eso `rotation 1 0 0 1.5708`. Si el
  mapa se ve girado o hundido, probar `-1.5708` (en `MAPA_ROTATION`, `gen_world.py`).

## Cronograma (3 meses / 12 semanas)

| Fase | Semanas | Descripcion |
|---|---|---|
| Diagnostico | 0 - 2 | Visitas de campo y medicion de cortes/consumo |
| Diseno y compras | 2 - 4 | Diseno tecnico y cotizacion de equipos |
| Instalacion piloto | 4 - 8 | Compra, instalacion de paneles/baterias y capacitacion |
| Pruebas y ajustes | 8 - 10 | Monitoreo y ajustes tecnicos |
| Entrega final | 10 - 12 | Socializacion con la comunidad y entrega de informe |

## Publicar en webots.cloud

1. Crear un repositorio **publico** en GitHub y subir el **contenido** de la
   carpeta `cienaga_solar_sim` en la raiz del repo (que `worlds/`,
   `controllers/` y `webots.yaml` queden en la raiz, no dentro de otra carpeta).
2. Ir a https://webots.cloud/demo e iniciar sesion.
3. Agregar la demo pegando la URL **del archivo del mundo** (no la del repo ni un zip), por ejemplo:
   `https://github.com/USUARIO/REPO/blob/main/worlds/cienaga_microgrid.wbt`
4. `webots.yaml` ya esta listo (`type: demo`, `publish: true`). No se incluye
   `Dockerfile` a proposito: sin el, webots.cloud usa el suyo por defecto.

Notas: la simulacion corre en el servidor de webots.cloud en modo streaming,
asi que la primera carga puede tardar (el mapa 3D pesa ~1.8 MB). Si falla,
revisar los mensajes de error que muestra la pagina de la demo.

## Estructura

```
cienaga_solar_sim/
├── webots.yaml
├── README.md
├── gen_world.py                  # genera worlds/cienaga_microgrid.wbt
├── worlds/
│   ├── cienaga_microgrid.wbt
│   └── meshes/ (cad-atlas_3D.obj, cad-atlas_3D.mtl)
├── controllers/grid_supervisor/grid_supervisor.py
└── blender/generar_casa_cienaga.py   # opcional
```
