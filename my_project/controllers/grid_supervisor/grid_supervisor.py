"""
Controlador Supervisor - Simulacion de respaldo solar en el barrio Kennedy (Cienaga).

Logica:
  - Cada cierto tiempo la "red electrica" (empresa de luz) falla -> CORTE.
  - Zona SIN panel solar: al cortarse la luz, las casas quedan completamente
    a oscuras (como pasa hoy en la realidad).
  - Zona CON panel solar de respaldo: al cortarse la luz, la bateria solar
    entra a operar y las casas siguen iluminadas (en color verde, para
    diferenciar visualmente "luz de red" de "luz solar de respaldo").
  - La bateria de la zona solar se descarga mientras opera en modo respaldo y
    se recarga cuando hay sol / red normal, para mostrar que no es una fuente
    infinita.
  - Un HUD (pantalla 2D) muestra el estado en tiempo real para la exposicion.
"""

from controller import Supervisor

TIME_STEP = 32

# Duraciones en pasos de simulacion (ajusta estos numeros para que la demo
# se vea mas rapida o mas lenta durante la exposicion)
STEPS_PER_SECOND = int(1000 / TIME_STEP)
GRID_UP_DURATION = 8 * STEPS_PER_SECOND     # segundos con luz normal
GRID_DOWN_DURATION = 6 * STEPS_PER_SECOND   # segundos de corte de luz

BATTERY_DRAIN_PER_STEP = 100.0 / GRID_DOWN_DURATION  # se agota justo al final del corte (peor caso)
BATTERY_CHARGE_PER_STEP = 100.0 / (GRID_UP_DURATION * 1.5)  # recarga mas lenta que el consumo

COLOR_OFF = [0.0, 0.0, 0.0]
COLOR_GRID_ON = [1.0, 0.85, 0.35]      # luz calida = viene de la red electrica
COLOR_SOLAR_ON = [0.25, 1.0, 0.35]     # luz verde = viene del respaldo solar/bateria
COLOR_TOWER_OK = [0.15, 0.9, 0.2]
COLOR_TOWER_FAIL = [1.0, 0.1, 0.1]

BARRIOS_SIN_SOLAR = {
    "Kennedy - sin panel": [f"NA{i}" for i in range(1, 10)] + [f"SA{i}" for i in range(1, 10)],
}
BARRIOS_CON_SOLAR = {
    "Kennedy - con panel": [f"NB{i}" for i in range(1, 10)] + [f"SB{i}" for i in range(1, 10)],
}

supervisor = Supervisor()

# --- localizar todos los campos de color de ventana ---
window_fields = {}
for grupo in (BARRIOS_SIN_SOLAR, BARRIOS_CON_SOLAR):
    for barrio, casas in grupo.items():
        for casa in casas:
            node = supervisor.getFromDef(f"WIN_{casa}_APP")
            if node is None:
                print(f"[AVISO] No se encontro el nodo WIN_{casa}_APP en el mundo")
                continue
            window_fields[casa] = node.getField("emissiveColor")

tower_node = supervisor.getFromDef("TOWER_LIGHT_APP")
tower_field = tower_node.getField("emissiveColor") if tower_node else None

display = supervisor.getDevice("hud")

# --- estado de baterias por barrio solar ---
battery_level = {barrio: 100.0 for barrio in BARRIOS_CON_SOLAR}

grid_up = True
timer = 0
blackout_count = 0

WHITE = 0xFFFFFF
BLACK = 0x000000
GREEN = 0x33FF55
RED = 0xFF3333
YELLOW = 0xFFD966
GRAY = 0x888888


def set_all_windows(casas, color):
    for casa in casas:
        field = window_fields.get(casa)
        if field:
            field.setSFColor(color)


def draw_hud():
    display.setColor(0x1a1a1a)
    display.fillRectangle(0, 0, 480, 260)

    display.setColor(WHITE)
    display.setFont("Arial", 14, True)
    display.drawText("Barrio Kennedy - Cienaga, Magdalena", 10, 8)

    estado_txt = "RED ELECTRICA: OK" if grid_up else "RED ELECTRICA: CORTE"
    display.setColor(GREEN if grid_up else RED)
    display.drawText(estado_txt, 10, 30)

    display.setColor(GRAY)
    display.drawText(f"Cortes simulados hasta ahora: {blackout_count}", 10, 50)

    display.setColor(WHITE)
    display.drawText("Zona SIN panel solar (se queda a oscuras):", 10, 78)
    y = 96
    for barrio in BARRIOS_SIN_SOLAR:
        color = YELLOW if grid_up else RED
        estado = "con luz (red)" if grid_up else "SIN LUZ"
        display.setColor(color)
        display.drawText(f"  - {barrio}: {estado}", 15, y)
        y += 18

    y += 8
    display.setColor(WHITE)
    display.drawText("Zona CON panel solar (mantiene la luz):", 10, y)
    y += 18
    for barrio in BARRIOS_CON_SOLAR:
        nivel = battery_level[barrio]
        fuente = "red electrica" if grid_up else "bateria solar"
        color = YELLOW if grid_up else GREEN
        display.setColor(color)
        display.drawText(f"  - {barrio}: {fuente} | bateria {nivel:4.0f}%", 15, y)
        y += 18
        # barra de bateria
        display.setColor(0x444444)
        display.fillRectangle(180, y - 14, 120, 10)
        bar_color = GREEN if nivel > 25 else RED
        display.setColor(bar_color)
        # Webots no acepta width=0 en fillRectangle, por eso solo dibujamos
        # la barra de nivel cuando hay algo que mostrar (ancho >= 1 pixel).
        ancho_barra = int(120 * nivel / 100)
        if ancho_barra > 0:
            display.fillRectangle(180, y - 14, ancho_barra, 10)
        y += 8


while supervisor.step(TIME_STEP) != -1:
    timer += 1

    if grid_up and timer >= GRID_UP_DURATION:
        grid_up = False
        timer = 0
        blackout_count += 1
        print(f"\n[EVENTO] Corte de luz #{blackout_count} en el barrio Kennedy, Cienaga.")
        print("  -> Zona SIN panel solar se queda SIN LUZ (situacion actual).")
        print("  -> Zona CON panel solar pasa a funcionar con BATERIA SOLAR.")
    elif not grid_up and timer >= GRID_DOWN_DURATION:
        grid_up = True
        timer = 0
        print("\n[EVENTO] Se restablecio el servicio de la red electrica en Kennedy.")
        print("  -> Toda la zona vuelve a alimentarse de la red.")
        print("  -> El panel solar empieza a recargar la bateria.")

    # --- actualizar barrios sin solar ---
    for barrio, casas in BARRIOS_SIN_SOLAR.items():
        set_all_windows(casas, COLOR_GRID_ON if grid_up else COLOR_OFF)

    # --- actualizar barrios con solar + baterias ---
    for barrio, casas in BARRIOS_CON_SOLAR.items():
        if grid_up:
            battery_level[barrio] = min(100.0, battery_level[barrio] + BATTERY_CHARGE_PER_STEP)
            set_all_windows(casas, COLOR_GRID_ON)
        else:
            if battery_level[barrio] > 0:
                battery_level[barrio] = max(0.0, battery_level[barrio] - BATTERY_DRAIN_PER_STEP)
                set_all_windows(casas, COLOR_SOLAR_ON)
            else:
                # caso extremo: si el corte dura demasiado y se agota la bateria
                set_all_windows(casas, COLOR_OFF)

    # --- torre electrica: verde si la red funciona, roja parpadeando si hay corte ---
    if tower_field:
        if grid_up:
            tower_field.setSFColor(COLOR_TOWER_OK)
        else:
            # parpadeo simple usando el contador de pasos
            tower_field.setSFColor(COLOR_TOWER_FAIL if (timer // 8) % 2 == 0 else COLOR_OFF)

    draw_hud()
