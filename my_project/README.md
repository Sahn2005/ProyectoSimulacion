# Microrred solar de respaldo - Barrio Kennedy, Cienaga (Magdalena)

Simulacion en **Webots** que representa la propuesta de proyecto final:
instalar paneles solares de respaldo en el barrio Kennedy de Cienaga,
Magdalena, para contrarrestar la inestabilidad del servicio de energia
electrica en la zona.

## 1. Idea del proyecto

En Cienaga el fluido electrico es muy inestable y la empresa prestadora
no resuelve los cortes frecuentes. La propuesta es instalar **paneles
solares con bateria de respaldo** en las viviendas del barrio Kennedy,
de forma que cuando se vaya la luz de la red publica, la energia
almacenada en la bateria mantenga las casas con servicio.

Para poder comparar visualmente el "antes" y el "despues" **dentro del
mismo barrio**, la simulacion divide Kennedy en dos zonas iguales:

| Zona | Casas | Que pasa en un corte de luz |
|---|---|---|
| **Sin panel solar** (situacion actual) | 18 casas (bloques Norte + Sur) | Las ventanas se apagan por completo |
| **Con panel solar + bateria** (propuesta) | 18 casas (bloques Norte + Sur) | Las ventanas siguen encendidas (en verde) usando la bateria |

## 2. Que se ve en la simulacion

- **36 casas en total** (18 sin solar + 18 con solar), con estilo de
  vivienda popular: bloque de concreto a la vista o pintura sencilla,
  techos de zinc inclinados o placa de concreto plana, rejas de
  seguridad en las ventanas — buscando parecerse a las viviendas reales
  del barrio Kennedy, no al estilo colonial turistico del centro de
  Cienaga.
- Una **torre/poste de la red electrica publica** con una luz que
  parpadea en rojo durante los cortes.
- Un letrero rojo frente a cada bloque sin panel solar y uno azul frente
  a cada bloque con panel solar, para identificarlos rapido desde lejos.
- Dos pantallas (`Display`) flotantes del robot supervisor:
  - **"hud"**: estado de la red (activa/corte), estado de cada zona y
    nivel de bateria de las zonas con panel solar.
  - **"cronograma"**: cronograma de implementacion del proyecto (ver
    seccion 6), que avanza **en vivo**, sincronizado con el reloj de la
    simulacion.

## 3. El mapa real de Cienaga

El mundo incluye el modelo CAD real del area de Cienaga que el usuario
aporto (`cad-atlas_3D.obj`, exportado desde Rhino), importado como una
malla (`Mesh`) dentro del nodo `DEF MAPA_CIENAGA_REAL`.

**Que es exactamente ese archivo:** es un levantamiento topografico/CAD
que contiene:
- Una malla triangulada continua que representa el **terreno** (altura
  variando suavemente entre ~2.3 m y ~9.1 m en toda el area).
- 33 curvas cerradas pequenas/medianas que representan **huellas de
  construcciones** (contornos de edificios, sin volumen ni techos
  modelados).
- 3 curvas cerradas gigantes que representan el **contorno del
  levantamiento/predio** (el limite del area digitalizada).

**Lo que el archivo NO tiene:** ninguna textura o foto satelital
incrustada (el `.mtl` original solo define 4 colores planos, sin ninguna
linea `map_Kd`), y ningun metadato de nombres de barrios, calles o
coordenadas geograficas. Por eso no es posible ubicar automaticamente en
que manzana exacta del archivo queda el barrio Kennedy o una direccion
puntual (se intento verificar contra una foto satelital de un punto de
referencia en Cienaga y no hay forma de confirmarlo solo con este
archivo).

**Por que las casas de Kennedy no estan "encima" del mapa real:** al no
haber etiquetas de ubicacion, las 36 casas se ubicaron en un lote
adyacente al mapa real (desplazado 100 m en el eje X, constante
`KENNEDY_X_OFFSET` en `gen_world.py`), para que la comparacion
"sin panel / con panel" sea clara y no quede encima de geometria real
sin saber si corresponde o no al barrio.

**Nota sobre los colores del mapa real:** Webots, al importar una malla
por `Mesh { url [...] }` directamente en el `.wbt`, no aplica
automaticamente los 4 materiales originales del `.obj` — se ve con el
color gris definido en el `PBRAppearance` del nodo `MAPA_CIENAGA_REAL`.
Si se quiere ver con sus colores originales, hay que importarlo con
**File > Import 3D Model...** desde el menu de Webots (no editando el
`.wbt` a mano), lo que crea los nodos de materiales automaticamente.

**Si el mapa se ve de lado o enterrado:** el archivo se genero en Rhino
(eje Y hacia arriba) y Webots usa Z hacia arriba, por eso el nodo tiene
`rotation 1 0 0 1.5708`. Si al abrir el mundo el mapa se ve girado o
hundido, cambiar ese valor a `-1.5708` en `worlds/cienaga_microgrid.wbt`
(nodo `DEF MAPA_CIENAGA_REAL`) y ajustar la `translation` en Z.

## 4. Instalacion

1. Instalar **Webots** (version R2023b o compatible):
   https://cyberbotics.com/
2. Descomprimir este proyecto en cualquier carpeta de tu PC.
3. Abrir Webots.
4. `File > Open World...` y seleccionar:
   `cienaga_solar_sim/worlds/cienaga_microgrid.wbt`

El controlador (`controllers/grid_supervisor/grid_supervisor.py`) se
carga automaticamente — no hay que configurar nada mas.

## 5. Como correr y ajustar la simulacion

- Dar play (▶) en la barra superior de Webots para iniciar la
  simulacion.
- Usar el mouse para rotar/mover la camara y ver ambas zonas de Kennedy
  y las dos pantallas del supervisor.

Parametros que se pueden ajustar en
`controllers/grid_supervisor/grid_supervisor.py`:

| Constante | Que controla |
|---|---|
| `GRID_UP_DURATION` | Segundos que dura la red electrica activa antes del siguiente corte |
| `GRID_DOWN_DURATION` | Segundos que dura cada corte de luz |
| `BATTERY_DRAIN_PER_STEP` | Velocidad de descarga de la bateria durante un corte |
| `BATTERY_CHARGE_PER_STEP` | Velocidad de recarga de la bateria con red activa |
| `CICLO_CRONOGRAMA_SEGUNDOS` | Cuantos segundos de simulacion equivalen a las 12 semanas completas del cronograma |

Si se cambia `gen_world.py` (por ejemplo la cantidad de casas o la
paleta de colores), hay que volver a ejecutarlo para regenerar el
`.wbt`:

```bash
python3 gen_world.py
```

## 6. Cronograma de implementacion (en vivo, dentro de la simulacion)

El cronograma no es una imagen estatica: la pantalla **"cronograma"**
del robot supervisor se redibuja cada paso de simulacion, resalta en
verde la fase activa y mueve una barra de progreso, todo sincronizado
con el reloj de la simulacion (`reloj_proyecto` en el controlador).

| Fase | Semanas | Descripcion |
|---|---|---|
| Diagnostico | 0 - 2 | Visitas de campo y medicion de cortes/consumo |
| Diseno y compras | 2 - 4 | Diseno tecnico del sistema y cotizacion de equipos |
| Instalacion piloto | 4 - 8 | Compra, instalacion de paneles/baterias y capacitacion |
| Pruebas y ajustes | 8 - 10 | Monitoreo de desempeno y ajustes tecnicos |
| Entrega final | 10 - 12 | Socializacion con la comunidad y entrega de informe |

Duracion total: **3 meses (12 semanas)**. Por defecto, una vuelta
completa del cronograma dura 60 segundos de simulacion (ajustable con
`CICLO_CRONOGRAMA_SEGUNDOS`), para que en una exposicion se pueda ver el
ciclo completo varias veces sin esperar minutos.

## 7. Modelo de casa mas detallado (opcional, Blender)

`blender/generar_casa_cienaga.py` genera en Blender un modelo de casa
con mas detalle (bloque, techo de zinc inclinado, panel solar) para
quien quiera reemplazar las cajas simples:

1. Abrir Blender > pestana "Scripting" > pegar el script > Run Script.
2. Exportar el objeto `CasaKennedy` como `.obj` o `.gltf`.
3. En Webots: `File > Import 3D Model...` y seleccionar el archivo
   exportado.

## 8. Publicar la simulacion en webots.cloud

Este proyecto ya incluye los dos archivos que exige webots.cloud:

- **`webots.yaml`** (en la raiz del proyecto): declara el tipo de
  publicacion.
  ```yaml
  type: demo
  publish: true
  ```
- **`Dockerfile`** (en la raiz del proyecto): define la imagen base con
  Webots instalado.
  ```dockerfile
  FROM cyberbotics/webots:R2023b-ubuntu22.04
  ARG PROJECT_PATH
  RUN mkdir -p $PROJECT_PATH
  COPY . $PROJECT_PATH
  ```

Pasos para publicarlo:

1. Subir esta carpeta completa a un repositorio de **GitHub** (publico
   o privado, segun lo que pida webots.cloud).
2. Ir a https://webots.cloud/demo
3. Seguir el flujo de "nuevo demo" pegando la URL del repositorio de
   GitHub. webots.cloud detecta `webots.yaml` y `Dockerfile`
   automaticamente y construye la demo para correrla en el navegador.

## 9. Guion sugerido para la exposicion

1. Mostrar el mundo completo (camara general) y explicar que ambas
   zonas son el mismo barrio Kennedy, divididas solo para comparar.
2. Esperar/forzar un corte de luz (`GRID_DOWN_DURATION`) y senalar que
   la zona sin panel se apaga mientras la zona con panel sigue
   encendida en verde.
3. Senalar la pantalla "hud" para mostrar el nivel de bateria bajando
   durante el corte y subiendo cuando vuelve la red.
4. Senalar la pantalla "cronograma" para explicar en que fase estaria
   el proyecto real y cuanto dura cada etapa.
5. Cerrar con el mapa real de Cienaga importado, aclarando que el lote
   de Kennedy se puso al lado porque el archivo CAD no trae etiquetas
   de barrios/calles.

## 10. Estructura del proyecto

```
cienaga_solar_sim/
├── webots.yaml
├── Dockerfile
├── README.md
├── gen_world.py                  # genera worlds/cienaga_microgrid.wbt
├── worlds/
│   ├── cienaga_microgrid.wbt
│   └── meshes/
│       ├── cad-atlas_3D.obj      # mapa real de Cienaga (aportado por el usuario)
│       └── cad-atlas_3D.mtl
├── controllers/
│   └── grid_supervisor/
│       └── grid_supervisor.py    # logica de cortes, bateria, HUD y cronograma
└── blender/
    └── generar_casa_cienaga.py   # modelo de casa opcional mas detallado
```
