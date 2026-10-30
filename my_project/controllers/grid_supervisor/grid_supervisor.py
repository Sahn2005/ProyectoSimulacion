"""
Controlador supervisor de la microrred solar sobre el mapa real de Cienaga.

  - Cortes periodicos del fluido electrico (situacion real en Cienaga).
  - Edificios SIN panel solar: se apagan por completo durante el corte.
  - Edificios CON panel solar + bateria: siguen encendidos (en verde) durante
    el corte mientras la bateria tenga carga. Los paneles SOLO cargan la
    bateria de dia (ciclo dia/noche con el sol moviendose en el cielo): un
    corte de noche descarga la bateria sin que nada la recargue.
  - HUD con estado de la red y nivel de bateria.
  - Cronograma del proyecto (3 meses / 12 semanas) en vivo, sincronizado con
    el reloj de la simulacion.
"""

import math
from controller import Supervisor

TIME_STEP = 32
STEPS_PER_SECOND = 1000.0 / TIME_STEP

# ---------------------------------------------------------------------------
# Ciclo de cortes de luz (ajustable para la exposicion)
# ---------------------------------------------------------------------------
GRID_UP_DURATION = 10.0     # segundos con red electrica activa
GRID_DOWN_DURATION = 6.0    # segundos de corte de luz

BATTERY_DRAIN_PER_STEP = 6.0 / STEPS_PER_SECOND    # % por segundo de consumo durante un corte
SOLAR_CHARGE_PER_STEP = 6.0 / STEPS_PER_SECOND     # % por segundo con el sol en el cenit

# Ciclo dia/noche: 24 horas simuladas duran DAY_DURATION segundos reales.
DAY_DURATION = 48.0
START_HOUR = 6.0                                   # la simulacion arranca al amanecer

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



# ---------------------------------------------------------------------------
# Bandera de Cienaga ondeando: cada franja vertical se desplaza en profundidad
# con una onda que viaja desde el asta hacia la punta (la amplitud crece con la
# distancia al asta) y se inclina siguiendo la pendiente de la onda.
# Los parametros de geometria deben coincidir con gen_world.py.
# ---------------------------------------------------------------------------
FLAG_STRIPS = 16
FLAG_W = 7.5
FLAG_Z = -3.0
WAVE_AMP = 0.7        # metros
WAVE_SPEED = 4.0      # rad/s
WAVE_LENGTHS = 1.3    # ondas a lo largo de la bandera

franjas = []
for _i in range(FLAG_STRIPS):
    _n = supervisor.getFromDef(f"FLAG_STRIP_{_i}")
    if _n is not None:
        franjas.append((_i, _n.getField("translation"), _n.getField("rotation")))
_flag_x = {}
for _i, _tr, _ro in franjas:
    _flag_x[_i] = _tr.getSFVec3f()[0]
_flag_y = franjas[0][1].getSFVec3f()[1] if franjas else 0.0


def ondear_bandera(t):
    for i, tr, ro in franjas:
        s = (i + 0.5) / FLAG_STRIPS
        fase = 2 * math.pi * WAVE_LENGTHS * s - WAVE_SPEED * t
        dz = WAVE_AMP * s * math.sin(fase)
        # d(dz)/dx con x = s * FLAG_W
        pendiente = WAVE_AMP * (math.sin(fase) + s * 2 * math.pi * WAVE_LENGTHS * math.cos(fase)) / FLAG_W
        tr.setSFVec3f([_flag_x[i], _flag_y, FLAG_Z + dz])
        ro.setSFRotation([0, 1, 0, -math.atan(pendiente)])

sol_node = supervisor.getFromDef("SOL")
cielo_node = supervisor.getFromDef("CIELO")
sol_dir = sol_node.getField("direction") if sol_node else None
sol_int = sol_node.getField("intensity") if sol_node else None
sol_amb = sol_node.getField("ambientIntensity") if sol_node else None
sol_col = sol_node.getField("color") if sol_node else None
cielo_col = cielo_node.getField("skyColor") if cielo_node else None
cielo_lum = cielo_node.getField("luminosity") if cielo_node else None


def _clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def _mezcla(c1, c2, k):
    return [c1[i] + (c2[i] - c1[i]) * k for i in range(3)]


def actualizar_cielo(hora):
    """Mueve el sol (este -> oeste), cambia color del cielo y luz ambiente.
    Devuelve la altura solar s en [-1, 1] (s > 0 = de dia)."""
    th = 2 * math.pi * (hora - 6.0) / 24.0
    s = math.sin(th)
    sx, sy, sz = 0.9 * math.cos(th), -0.35, s
    n = math.sqrt(sx * sx + sy * sy + sz * sz)
    dia_dir = (-sx / n, -sy / n, -sz / n)
    luna_dir = (0.2, -0.3, -0.9)
    noche = 1.0 - _clamp(s * 3.0)
    d = [dia_dir[i] + (luna_dir[i] - dia_dir[i]) * noche for i in range(3)]
    dn = math.sqrt(sum(c * c for c in d))
    if sol_dir:
        sol_dir.setSFVec3f([c / dn for c in d])
        sol_int.setSFFloat(2.5 * (_clamp(s) ** 0.6) + 0.3 * noche)
        sol_amb.setSFFloat(0.1 + 0.25 * (1.0 - noche))
        calido = _mezcla([1.0, 0.55, 0.35], [1.0, 0.97, 0.9], _clamp(s * 3.0))
        sol_col.setSFColor(_mezcla(calido, [0.55, 0.65, 1.0], noche))
    if cielo_col:
        dia, noche_c, ocaso = [0.55, 0.75, 0.95], [0.02, 0.03, 0.09], [0.9, 0.5, 0.3]
        k = _clamp((s + 0.1) / 0.5)
        c = _mezcla(noche_c, dia, k)
        c = _mezcla(c, ocaso, 0.5 * _clamp(1.0 - abs(s - 0.05) / 0.2))
        cielo_col.setMFColor(0, c)
        cielo_lum.setSFFloat(0.15 + 0.85 * k)
    return s


ventanas_sin_solar = buscar_ventanas("RNOS")
ventanas_con_solar = buscar_ventanas("RSOL")

print(f"[grid_supervisor] franjas de bandera: {len(franjas)}")
print(f"[grid_supervisor] ventanas sin solar: {len(ventanas_sin_solar)}, "
      f"con solar: {len(ventanas_con_solar)}, torre: {'ok' if tower_field else 'NO ENCONTRADA'}")
if hud is None or cronograma_display is None:
    print("[grid_supervisor] ERROR: no se encontraron los Display 'hud'/'cronograma'")

bateria = 70.0
sol_altura = 1.0
hora_sim = START_HOUR
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
    produccion = max(0.0, sol_altura)
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
        hud.drawText("Con luz (red publica + paneles)", 20, 138)
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

    hh = int(hora_sim) % 24
    mm = int((hora_sim - int(hora_sim)) * 60)
    hud.setColor(0xFFDD66 if sol_altura > 0 else 0x8899FF)
    hud.drawText(f"{'DIA' if sol_altura > 0 else 'NOCHE'}  {hh:02d}:{mm:02d}   Produccion solar: {int(produccion * 100):3d}%", 10, 192)
    hud.setColor(0x444444)
    hud.fillRectangle(20, 216, 200, 12)
    if produccion > 0:
        hud.setColor(0xFFCC33)
        hud.fillRectangle(20, 216, max(1, int(200 * produccion)), 12)


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

    # --- dia/noche: sol y cielo ---
    hora_sim = (START_HOUR + 24.0 * reloj_proyecto / DAY_DURATION) % 24.0
    if paso % 2 == 0:
        sol_altura = actualizar_cielo(hora_sim)

    # --- bateria: los paneles solo cargan de dia; el corte la descarga ---
    carga_solar = SOLAR_CHARGE_PER_STEP * max(0.0, sol_altura)
    consumo = 0.0 if grid_up else BATTERY_DRAIN_PER_STEP
    bateria = max(0.0, min(100.0, bateria + carga_solar - consumo))

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

    # --- bandera ondeando ---
    ondear_bandera(reloj_proyecto)

    # --- pantallas (cada 3 pasos para no recargar la simulacion) ---
    if paso % 3 == 0:
        semana = (reloj_proyecto % CICLO_CRONOGRAMA_SEGUNDOS) / SEGUNDOS_POR_SEMANA
        draw_hud(grid_up)
        draw_cronograma(semana)
