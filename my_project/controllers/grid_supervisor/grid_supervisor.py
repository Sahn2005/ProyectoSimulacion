"""
Controlador supervisor de la microrred del barrio Kennedy - Cienaga.

Simula:
  - Cortes periodicos del fluido electrico (situacion real en Cienaga).
  - Zona SIN panel solar: se apaga por completo durante el corte.
  - Zona CON panel solar + bateria de respaldo: se mantiene encendida
    durante el corte, usando la energia almacenada, y la bateria se
    recarga con el panel mientras hay sol / red activa.
  - Un HUD con el estado de cada zona y el nivel de bateria.
  - Un cronograma de implementacion del proyecto (3 meses / 12 semanas)
    que avanza en vivo, sincronizado con el reloj de la simulacion.
"""

from controller import Supervisor

TIME_STEP = 32
STEPS_PER_SECOND = 1000.0 / TIME_STEP

# ---------------------------------------------------------------------------
# Ciclo de cortes de luz (ajustable para la exposicion)
# ---------------------------------------------------------------------------
GRID_UP_DURATION = 10.0     # segundos con red electrica activa
GRID_DOWN_DURATION = 6.0    # segundos de corte de luz

BATTERY_DRAIN_PER_STEP = 0.9 / STEPS_PER_SECOND   # % de bateria que se gasta por segundo en corte
BATTERY_CHARGE_PER_STEP = 1.6 / STEPS_PER_SECOND  # % de bateria que se recupera por segundo con red activa

COLOR_OFF = (0.0, 0.0, 0.0)
COLOR_GRID_ON = (0.95, 0.9, 0.55)      # luz calida normal (red publica)
COLOR_SOLAR_ON = (0.3, 0.95, 0.5)      # luz verde: funcionando con respaldo solar
COLOR_TOWER_OK = (0.2, 0.9, 0.3)
COLOR_TOWER_FAIL = (0.95, 0.15, 0.1)

# ---------------------------------------------------------------------------
# Zonas y casas (36 casas: 18 sin solar, 18 con solar)
# ---------------------------------------------------------------------------
BARRIOS_SIN_SOLAR = {
    "Kennedy - Zona sin panel solar": [f"NA{i}" for i in range(1, 10)] + [f"SA{i}" for i in range(1, 10)],
}
BARRIOS_CON_SOLAR = {
    "Kennedy - Zona con panel solar": [f"NB{i}" for i in range(1, 10)] + [f"SB{i}" for i in range(1, 10)],
}

# ---------------------------------------------------------------------------
# Cronograma del proyecto (3 meses = 12 semanas), sincronizado con el reloj
# de la simulacion para que avance solo mientras esta corre.
# ---------------------------------------------------------------------------
CICLO_CRONOGRAMA_SEGUNDOS = 60.0   # 1 vuelta completa de cronograma = 60s de simulacion
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

tower_light = supervisor.getFromDef("TOWER_LIGHT_APP")


def get_window_field(casa_id):
    node = supervisor.getFromDef(f"WIN_{casa_id}_APP")
    if node is None:
        return None
    return node.getField("emissiveColor")


ventanas_sin_solar = {
    nombre: [get_window_field(cid) for cid in casas]
    for nombre, casas in BARRIOS_SIN_SOLAR.items()
}
ventanas_con_solar = {
    nombre: [get_window_field(cid) for cid in casas]
    for nombre, casas in BARRIOS_CON_SOLAR.items()
}

bateria = {nombre: 100.0 for nombre in BARRIOS_CON_SOLAR}

grid_up = True
grid_timer = 0.0
reloj_proyecto = 0.0


def set_color_all(campos, color):
    for campo in campos:
        if campo is not None:
            campo.setSFColor(list(color))


def draw_hud(grid_activa, semana_actual):
    hud.setColor(0x202020)
    hud.fillRectangle(0, 0, 480, 260)

    hud.setColor(0xFFFFFF)
    hud.setFont("Arial", 16, True)
    hud.drawText("Microrred Kennedy - Cienaga, Magdalena", 10, 8)

    hud.setFont("Arial", 13, True)
    estado_red = "RED ELECTRICA: ACTIVA" if grid_activa else "RED ELECTRICA: CORTE"
    hud.setColor(0x55FF66 if grid_activa else 0xFF4433)
    hud.drawText(estado_red, 10, 34)

    y = 64
    hud.setColor(0xCCCCCC)
    hud.setFont("Arial", 12, False)
    for nombre in BARRIOS_SIN_SOLAR:
        hud.drawText(f"{nombre}:", 10, y)
        hud.setColor(0xFF5544 if not grid_activa else 0xFFCC55)
        hud.drawText("SIN LUZ (corte)" if not grid_activa else "Con luz (red publica)", 20, y + 18)
        hud.setColor(0xCCCCCC)
        y += 46

    for nombre in BARRIOS_CON_SOLAR:
        nivel = bateria[nombre]
        hud.drawText(f"{nombre}:", 10, y)
        hud.setColor(0x55DD88)
        estado = "Con luz (bateria solar)" if not grid_activa else "Con luz (red + cargando bateria)"
        hud.drawText(estado, 20, y + 18)

        hud.setColor(0x444444)
        hud.fillRectangle(20, y + 36, 200, 14)
        ancho_barra = int(2 * nivel)
        if ancho_barra > 0:
            color_barra = 0x33CC66 if nivel > 30 else 0xDD8822
            hud.setColor(color_barra)
            hud.fillRectangle(20, y + 36, ancho_barra, 14)
        hud.setColor(0xFFFFFF)
        hud.drawText(f"Bateria: {nivel:4.1f}%", 230, y + 34)
        hud.setColor(0xCCCCCC)
        y += 62


def draw_cronograma(semana_actual):
    W, H = 620, 300
    cronograma_display.setColor(0x151515)
    cronograma_display.fillRectangle(0, 0, W, H)

    cronograma_display.setColor(0xFFFFFF)
    cronograma_display.setFont("Arial", 15, True)
    cronograma_display.drawText("Cronograma de implementacion (3 meses / 12 semanas)", 10, 8)

    mes = int(semana_actual // 4.33) + 1
    mes = min(mes, 3)
    cronograma_display.setFont("Arial", 12, False)
    cronograma_display.setColor(0xAAAAAA)
    cronograma_display.drawText(
        f"Semana {semana_actual:4.1f} de {SEMANAS_TOTALES}  (Mes {mes})", 10, 30)

    top = 56
    row_h = 40
    for nombre, ini, fin, detalle in FASES:
        activa = ini <= semana_actual < fin
        color_fondo = 0x2E7D32 if activa else 0x262626
        cronograma_display.setColor(color_fondo)
        cronograma_display.fillRectangle(10, top, W - 20, row_h - 6)

        cronograma_display.setColor(0xFFFFFF if activa else 0x999999)
        cronograma_display.setFont("Arial", 12, True)
        cronograma_display.drawText(nombre, 18, top + 4)
        cronograma_display.setFont("Arial", 10, False)
        cronograma_display.drawText(detalle, 18, top + 20)
        top += row_h

    barra_y = top + 10
    cronograma_display.setColor(0x333333)
    cronograma_display.fillRectangle(10, barra_y, W - 20, 16)
    progreso = int((W - 20) * (semana_actual / SEMANAS_TOTALES))
    if progreso > 0:
        cronograma_display.setColor(0x4CAF50)
        cronograma_display.fillRectangle(10, barra_y, progreso, 16)


while supervisor.step(TIME_STEP) != -1:
    dt = TIME_STEP / 1000.0

    # --- ciclo de cortes de luz ---
    grid_timer += dt
    if grid_up and grid_timer >= GRID_UP_DURATION:
        grid_up = False
        grid_timer = 0.0
    elif (not grid_up) and grid_timer >= GRID_DOWN_DURATION:
        grid_up = True
        grid_timer = 0.0

    # --- zonas sin panel solar: dependen 100% de la red ---
    color_actual = COLOR_GRID_ON if grid_up else COLOR_OFF
    for campos in ventanas_sin_solar.values():
        set_color_all(campos, color_actual)

    # --- zonas con panel solar + bateria ---
    for nombre, campos in ventanas_con_solar.items():
        if grid_up:
            bateria[nombre] = min(100.0, bateria[nombre] + BATTERY_CHARGE_PER_STEP)
            set_color_all(campos, COLOR_GRID_ON)
        else:
            bateria[nombre] = max(0.0, bateria[nombre] - BATTERY_DRAIN_PER_STEP)
            if bateria[nombre] > 0:
                set_color_all(campos, COLOR_SOLAR_ON)
            else:
                set_color_all(campos, COLOR_OFF)

    # --- torre de la red publica: parpadeo rojo cuando hay corte ---
    if tower_light is not None:
        campo_torre = tower_light.getField("emissiveColor")
        if grid_up:
            campo_torre.setSFColor(list(COLOR_TOWER_OK))
        else:
            parpadeo = int(reloj_proyecto * 4) % 2 == 0
            campo_torre.setSFColor(list(COLOR_TOWER_FAIL) if parpadeo else list(COLOR_OFF))

    # --- reloj del proyecto / cronograma en vivo ---
    reloj_proyecto += dt
    semana_actual = (reloj_proyecto % CICLO_CRONOGRAMA_SEGUNDOS) / SEGUNDOS_POR_SEMANA

    draw_hud(grid_up, semana_actual)
    draw_cronograma(semana_actual)
