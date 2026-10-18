"""
Controlador supervisor de la microrred solar sobre el mapa real de Cienaga.

  - Cortes periodicos del fluido electrico (situacion real en Cienaga).
  - Edificios SIN panel solar: se apagan por completo durante el corte.
  - Edificios CON panel solar + bateria: siguen encendidos (en verde) durante
    el corte mientras la bateria tenga carga; con la red activa la recargan.
  - HUD con estado de la red y nivel de bateria.
  - Cronograma del proyecto (3 meses / 12 semanas) en vivo, sincronizado con
    el reloj de la simulacion.
"""

from controller import Supervisor

TIME_STEP = 32
STEPS_PER_SECOND = 1000.0 / TIME_STEP

# ---------------------------------------------------------------------------
# Ciclo de cortes de luz (ajustable para la exposicion)
# ---------------------------------------------------------------------------
GRID_UP_DURATION = 10.0     # segundos con red electrica activa
GRID_DOWN_DURATION = 6.0    # segundos de corte de luz

BATTERY_DRAIN_PER_STEP = 5.0 / STEPS_PER_SECOND    # % por segundo en corte (6 s -> ~30 %)
BATTERY_CHARGE_PER_STEP = 8.0 / STEPS_PER_SECOND   # % por segundo con red activa

COLOR_OFF = (0.0, 0.0, 0.0)
COLOR_GRID_ON = (0.95, 0.85, 0.35)     # luz calida (red publica)
COLOR_SOLAR_ON = (0.2, 1.0, 0.45)      # luz verde (respaldo solar)
COLOR_TOWER_OK = (0.2, 0.9, 0.3)
COLOR_TOWER_FAIL = (0.95, 0.15, 0.1)

# ---------------------------------------------------------------------------
# Cronograma del proyecto (3 meses = 12 semanas)
# ---------------------------------------------------------------------------
CICLO_CRONOGRAMA_SEGUNDOS = 60.0
SEMANAS_TOTALES = 12
SEGUNDOS_POR_SEMANA = CICLO_CRONOGRAMA_SEGUNDOS / SEMANAS_TOTALES

FASES = [
    ("Diagnostico",        0,  2,  "Visitas de campo y medicion de cortes/consumo"),
    ("Diseno y compras",   2,  4,  "Diseno tecnico del sistema y cotizacion de equipos"),
    ("Instalacion piloto", 4,  8,  "Compra, instalacion de paneles/baterias y capacitacion"),
    ("Pruebas y ajustes",  8,  10, "Monitoreo de desempeno y ajustes tecnicos"),
    ("Entrega final",      10, 12, "Socializacion con la comunidad y entrega de informe"),
]

supervisor = Supervisor()

hud = supervisor.getDevice("hud")
cronograma_display = supervisor.getDevice("cronograma")
tower_node = supervisor.getFromDef("TOWER_LIGHT_APP")
tower_field = tower_node.getField("emissiveColor") if tower_node else None


def buscar_ventanas(grupo):
    """Recoge los campos emissiveColor de WIN_<grupo>_1_APP, _2_APP, ... hasta
    que no exista el siguiente (asi no hay que fijar la cantidad a mano)."""
    campos = []
    i = 1
    while True:
        nodo = supervisor.getFromDef(f"WIN_{grupo}_{i}_APP")
        if nodo is None:
            break
        campos.append(nodo.getField("emissiveColor"))
        i += 1
    return campos


ventanas_sin_solar = buscar_ventanas("RNOS")
ventanas_con_solar = buscar_ventanas("RSOL")

print(f"[grid_supervisor] ventanas sin solar: {len(ventanas_sin_solar)}, "
      f"con solar: {len(ventanas_con_solar)}, torre: {'ok' if tower_field else 'NO ENCONTRADA'}")
if hud is None or cronograma_display is None:
    print("[grid_supervisor] ERROR: no se encontraron los Display 'hud'/'cronograma'")

bateria = 100.0
grid_up = True
grid_timer = 0.0
reloj_proyecto = 0.0

# ultimo color aplicado a cada grupo (solo se escribe cuando cambia)
ultimo_sin = None
ultimo_con = None


def set_color_all(campos, color):
    valor = list(color)
    for campo in campos:
        campo.setSFColor(valor)


def draw_hud(grid_activa):
    hud.setColor(0x202020)
    hud.fillRectangle(0, 0, 480, 260)

    hud.setColor(0xFFFFFF)
    hud.setFont("Arial", 16, True)
    hud.drawText("Microrred solar - Cienaga, Magdalena", 10, 8)

    hud.setFont("Arial", 13, True)
    hud.setColor(0x55FF66 if grid_activa else 0xFF4433)
    hud.drawText("RED ELECTRICA: ACTIVA" if grid_activa else "RED ELECTRICA: CORTE", 10, 34)

    hud.setFont("Arial", 12, False)
    hud.setColor(0xCCCCCC)
    hud.drawText("Edificios SIN panel solar (situacion actual):", 10, 66)
    hud.setColor(0xFFCC55 if grid_activa else 0xFF5544)
    hud.drawText("Con luz (red publica)" if grid_activa else "SIN LUZ (corte)", 20, 84)

    hud.setColor(0xCCCCCC)
    hud.drawText("Edificios CON panel solar + bateria (propuesta):", 10, 120)
    hud.setColor(0x55DD88)
    if grid_activa:
        hud.drawText("Con luz (red + cargando bateria)", 20, 138)
    else:
        hud.drawText("Con luz (bateria solar)" if bateria > 0 else "SIN LUZ (bateria agotada)", 20, 138)

    hud.setColor(0x444444)
    hud.fillRectangle(20, 164, 200, 14)
    ancho = int(2 * bateria)
    if ancho > 0:
        hud.setColor(0x33CC66 if bateria > 30 else 0xDD8822)
        hud.fillRectangle(20, 164, ancho, 14)
    hud.setColor(0xFFFFFF)
    hud.drawText(f"Bateria: {bateria:5.1f}%", 230, 162)


def draw_cronograma(semana_actual):
    W = 620
    d = cronograma_display
    d.setColor(0x151515)
    d.fillRectangle(0, 0, W, 300)

    d.setColor(0xFFFFFF)
    d.setFont("Arial", 15, True)
    d.drawText("Cronograma de implementacion (3 meses / 12 semanas)", 10, 8)

    mes = min(int(semana_actual // 4.0) + 1, 3)
    d.setFont("Arial", 12, False)
    d.setColor(0xAAAAAA)
    d.drawText(f"Semana {semana_actual:4.1f} de {SEMANAS_TOTALES}  (Mes {mes})", 10, 30)

    top = 56
    for nombre, ini, fin, detalle in FASES:
        activa = ini <= semana_actual < fin
        d.setColor(0x2E7D32 if activa else 0x262626)
        d.fillRectangle(10, top, W - 20, 34)
        d.setColor(0xFFFFFF if activa else 0x999999)
        d.setFont("Arial", 12, True)
        d.drawText(nombre, 18, top + 4)
        d.setFont("Arial", 10, False)
        d.drawText(detalle, 18, top + 20)
        top += 40

    barra_y = top + 10
    d.setColor(0x333333)
    d.fillRectangle(10, barra_y, W - 20, 16)
    progreso = int((W - 20) * (semana_actual / SEMANAS_TOTALES))
    if progreso > 0:
        d.setColor(0x4CAF50)
        d.fillRectangle(10, barra_y, progreso, 16)


paso = 0
while supervisor.step(TIME_STEP) != -1:
    dt = TIME_STEP / 1000.0
    paso += 1

    # --- ciclo de cortes de luz ---
    grid_timer += dt
    if grid_up and grid_timer >= GRID_UP_DURATION:
        grid_up, grid_timer = False, 0.0
    elif (not grid_up) and grid_timer >= GRID_DOWN_DURATION:
        grid_up, grid_timer = True, 0.0

    # --- bateria ---
    if grid_up:
        bateria = min(100.0, bateria + BATTERY_CHARGE_PER_STEP)
    else:
        bateria = max(0.0, bateria - BATTERY_DRAIN_PER_STEP)

    # --- ventanas: solo se escriben cuando cambia el color ---
    color_sin = COLOR_GRID_ON if grid_up else COLOR_OFF
    if grid_up:
        color_con = COLOR_GRID_ON
    else:
        color_con = COLOR_SOLAR_ON if bateria > 0 else COLOR_OFF

    if color_sin != ultimo_sin:
        set_color_all(ventanas_sin_solar, color_sin)
        ultimo_sin = color_sin
    if color_con != ultimo_con:
        set_color_all(ventanas_con_solar, color_con)
        ultimo_con = color_con

    # --- torre de la red publica: parpadeo rojo durante el corte ---
    reloj_proyecto += dt
    if tower_field is not None:
        if grid_up:
            tower_field.setSFColor(list(COLOR_TOWER_OK))
        else:
            parpadeo = int(reloj_proyecto * 4) % 2 == 0
            tower_field.setSFColor(list(COLOR_TOWER_FAIL) if parpadeo else list(COLOR_OFF))

    # --- pantallas (cada 3 pasos para no recargar la simulacion) ---
    if paso % 3 == 0:
        semana = (reloj_proyecto % CICLO_CRONOGRAMA_SEGUNDOS) / SEGUNDOS_POR_SEMANA
        draw_hud(grid_up)
        draw_cronograma(semana)
