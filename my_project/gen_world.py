"""
Generador del archivo .wbt para la simulacion de microrred solar sobre el
mapa real de Cienaga (levantamiento CAD aportado por el usuario).

Se ejecuta cada vez que se quiera regenerar el mundo:
    python3 gen_world.py
"""
import math
import os
import random

# Todo se coloca como hijo de un Solid que comparte translation/rotation con
# la malla del mapa real, asi cada edificio queda alineado con el terreno.
# Coordenadas locales: x y z del .obj (Rhino: Y es la altura).
MAPA_TRANSLATION = "0 0 -2.26"
MAPA_ROTATION = "1 0 0 1.5708"
ALTURA_EDIFICIO_REAL = 3.4

# True  -> la mitad de los edificios con panel y la otra mitad sin (comparacion)
# False -> todos los edificios que puedan llevar panel lo tienen
COMPARAR_CON_Y_SIN_SOLAR = True

# (cx, cy, cz, dx, dz): huellas de construccion extraidas de las curvas
# cerradas del CAD original. 1 huella degenerada (0.6 x 0.08 m) se descarto.
EDIFICIOS_REALES = [
    (-54.62, 2.71, 15.58, 14.07, 11.65),
    (11.84, 2.58, 9.80, 6.45, 11.65),
    (-53.77, 2.51, 40.42, 23.07, 32.12),
    (60.50, 2.53, 6.73, 1.17, 4.80),
    (-20.40, 2.67, 0.59, 4.69, 8.74),
    (-58.54, 2.88, -0.08, 7.04, 24.17),
    (52.41, 2.50, 48.12, 4.69, 10.49),
    (-19.68, 2.56, 16.95, 15.24, 21.55),
    (-30.22, 3.02, -52.59, 7.07, 5.70),
    (12.19, 2.49, 33.33, 6.45, 7.57),
    (-27.08, 2.67, 2.69, 9.97, 9.90),
    (-60.09, 3.02, -14.84, 1.76, 8.39),
    (23.03, 2.43, 51.77, 7.87, 7.07),
    (24.45, 2.51, 34.68, 11.14, 20.39),
    (-16.31, 2.95, -53.34, 43.64, 3.95),
    (-60.85, 2.70, 19.62, 0.59, 4.25),
    (-5.51, 2.77, -32.26, 9.38, 18.64),
    (27.32, 2.59, -4.07, 22.86, 14.56),
    (12.19, 2.43, 44.51, 15.24, 15.14),
    (-27.39, 2.92, -34.36, 25.21, 22.72),
    (24.97, 2.63, -22.47, 11.14, 18.64),
    (15.12, 2.55, 19.23, 5.28, 4.08),
    (58.98, 2.54, 1.41, 4.10, 6.50),
    (14.91, 2.71, -35.55, 19.93, 18.06),
    (18.29, 2.49, 35.08, 9.38, 20.97),
    (-56.06, 2.43, 52.70, 6.54, 4.74),
    (-1.17, 2.80, -46.12, 5.86, 5.24),
    (43.15, 2.52, 32.98, 11.14, 8.15),
    (41.76, 2.48, 49.32, 17.16, 12.31),
    (33.31, 2.56, 16.89, 21.10, 27.96),
    (-25.79, 2.76, -10.33, 17.00, 15.73),
    (-43.93, 3.10, -49.86, 9.38, 11.52),
]

PANEL_W, PANEL_D = 1.6, 1.0   # tamano de cada panel (m)


def paneles_que_caben(dx, dz):
    nx = min(4, int((dx - 1.0) // (PANEL_W + 0.3)))
    nz = min(3, int((dz - 1.0) // (PANEL_D + 0.3)))
    return max(nx, 0), max(nz, 0)


_ventana_counter = {"RSOL": 0, "RNOS": 0}


def ventana(grupo, cx, y, cz, size):
    _ventana_counter[grupo] += 1
    n = _ventana_counter[grupo]
    return f"""
    Transform {{
      translation {cx:.3f} {y:.3f} {cz:.3f}
      children [
        Shape {{
          appearance DEF WIN_{grupo}_{n}_APP PBRAppearance {{
            baseColor 0.04 0.04 0.05
            emissiveColor 0 0 0
            emissiveIntensity 3
            roughness 0.4
          }}
          geometry Box {{
            size {size}
          }}
        }}
      ]
    }}"""


def paneles_techo(cx, cy, cz, dx, dz, nx, nz):
    y_techo = cy + ALTURA_EDIFICIO_REAL + 0.25
    out = ""
    paso_x = PANEL_W + 0.3
    paso_z = PANEL_D + 0.3
    x0 = cx - (nx - 1) * paso_x / 2
    z0 = cz - (nz - 1) * paso_z / 2
    for i in range(nx):
        for j in range(nz):
            out += f"""
    Transform {{
      translation {x0 + i * paso_x:.3f} {y_techo:.3f} {z0 + j * paso_z:.3f}
      rotation 1 0 0 0.25
      children [
        Shape {{
          appearance PBRAppearance {{
            baseColor 0.05 0.08 0.25
            metalness 0.6
            roughness 0.3
          }}
          geometry Box {{
            size {PANEL_W} 0.06 {PANEL_D}
          }}
        }}
      ]
    }}"""
    return out


# Paleta de fachadas de barrio popular costeno (pared, techo, tipo de techo):
# bloque de concreto sin pintar o pintura sencilla y desgastada, con techo de
# losa de concreto o de zinc. Cada edificio toma un color del ciclo.
PALETA_FACHADAS = [
    ("0.68 0.66 0.62", "0.78 0.78 0.75", "losa"),   # concreto sin pintar
    ("0.55 0.68 0.78", "0.58 0.58 0.60", "zinc"),   # celeste desgastado
    ("0.80 0.60 0.55", "0.78 0.78 0.75", "losa"),   # salmon
    ("0.63 0.72 0.60", "0.58 0.58 0.60", "zinc"),   # verde palido
    ("0.82 0.74 0.50", "0.58 0.58 0.60", "zinc"),   # amarillo/beige
    ("0.72 0.52 0.42", "0.78 0.78 0.75", "losa"),   # terracota
    ("0.85 0.82 0.75", "0.58 0.58 0.60", "zinc"),   # blanco hueso
]
_fachada_counter = [0]


def _mat(nombre, base, extra=""):
    if nombre in _fachada_defs:
        return f"USE {nombre}"
    _fachada_defs.add(nombre)
    return f"DEF {nombre} PBRAppearance {{ baseColor {base} roughness 0.92 {extra} }}"


_fachada_defs = set()


def edificio(cx, cy, cz, dx, dz, solar):
    grupo = "RSOL" if solar else "RNOS"
    base = cy + ALTURA_EDIFICIO_REAL / 2.0
    yv = cy + ALTURA_EDIFICIO_REAL * 0.55
    extra = ""

    n_x = max(1, min(5, round(dx / 3.5)))
    paso_x = dx / (n_x + 1)
    for k in range(1, n_x + 1):
        px = cx - dx / 2 + k * paso_x
        for borde in (dz / 2 + 0.03, -dz / 2 - 0.03):
            extra += ventana(grupo, px, yv, cz + borde, "0.55 0.55 0.04")

    n_z = max(1, min(5, round(dz / 3.5)))
    paso_z = dz / (n_z + 1)
    for k in range(1, n_z + 1):
        pz = cz - dz / 2 + k * paso_z
        for borde in (dx / 2 + 0.03, -dx / 2 - 0.03):
            extra += ventana(grupo, cx + borde, yv, pz, "0.04 0.55 0.55")

    if solar:
        nx, nz = paneles_que_caben(dx, dz)
        extra += paneles_techo(cx, cy, cz, dx, dz, nx, nz)

    acera = _mat("ACERA_APP", "0.62 0.61 0.58")
    k = _fachada_counter[0] % len(PALETA_FACHADAS)
    _fachada_counter[0] += 1
    pared, techo, tipo = PALETA_FACHADAS[k]
    mat_pared = _mat(f"PARED_{k}_APP", pared)
    mat_techo = _mat(f"TECHO_{k}_APP", techo, "metalness 0.25" if tipo == "zinc" else "")
    return f"""
Transform {{
  translation {cx:.3f} {cy + 0.05:.3f} {cz:.3f}
  children [
    Shape {{
      appearance {acera}
      geometry Box {{
        size {dx + 1.8:.3f} 0.14 {dz + 1.8:.3f}
      }}
    }}
  ]
}}
Transform {{
  translation {cx:.3f} {base:.3f} {cz:.3f}
  children [
    Shape {{
      appearance {mat_pared}
      geometry Box {{
        size {dx:.3f} {ALTURA_EDIFICIO_REAL} {dz:.3f}
      }}
    }}
  ]
}}
Transform {{
  translation {cx:.3f} {cy + ALTURA_EDIFICIO_REAL + 0.075:.3f} {cz:.3f}
  children [
    Shape {{
      appearance {mat_techo}
      geometry Box {{
        size {dx + 0.3:.3f} 0.15 {dz + 0.3:.3f}
      }}
    }}
  ]
}}{extra}
"""


def torre():
    # Torre de la red publica en el centro del mapa (Boxes: no dependen del
    # eje del cilindro). Coordenadas locales: y = altura.
    return """
Transform {
  translation 0 7.1 0
  children [
    Shape {
      appearance PBRAppearance { baseColor 0.3 0.3 0.3 metalness 0.7 roughness 0.4 }
      geometry Box { size 0.6 9 0.6 }
    }
    Transform {
      translation 0 4.6 0
      children [
        Shape {
          appearance PBRAppearance { baseColor 0.3 0.3 0.3 metalness 0.7 roughness 0.4 }
          geometry Box { size 3.2 0.2 0.2 }
        }
      ]
    }
    Transform {
      translation 0 5.2 0
      children [
        Shape {
          appearance DEF TOWER_LIGHT_APP PBRAppearance {
            baseColor 0.2 0.2 0.2
            emissiveColor 0 0 0
            emissiveIntensity 3
          }
          geometry Sphere { radius 0.4 }
        }
      ]
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# Bandera de Cienaga (dos franjas horizontales iguales: amarillo arriba,
# verde abajo). Va en la plazoleta libre del centro del mapa, a la izquierda
# de la torre, donde se ve bien desde la camara inicial y no choca con
# ningun edificio. Se compone de franjas verticales que el controlador mueve
# en cada paso para que ondee. FLAG_Y es la altura del terreno en ese punto.
# ---------------------------------------------------------------------------
FLAG_X, FLAG_Z, FLAG_Y = -14.0, -3.0, 2.68
FLAG_POLE_H = 14.0
FLAG_W, FLAG_H = 7.5, 5.0          # proporcion 3:2
FLAG_STRIPS = 16


def bandera():
    w = FLAG_W / FLAG_STRIPS
    y_top = FLAG_Y + FLAG_POLE_H - 0.4          # borde superior de la tela
    y_mid = y_top - FLAG_H / 4.0
    y_bot = y_top - 3.0 * FLAG_H / 4.0
    x_hoist = FLAG_X + 0.15
    out = f"""
Transform {{
  translation {FLAG_X} {FLAG_Y + FLAG_POLE_H / 2:.3f} {FLAG_Z}
  children [
    Shape {{
      appearance PBRAppearance {{ baseColor 0.75 0.75 0.78 metalness 0.8 roughness 0.35 }}
      geometry Box {{ size 0.3 {FLAG_POLE_H} 0.3 }}
    }}
  ]
}}
Transform {{
  translation {FLAG_X} {FLAG_Y + FLAG_POLE_H + 0.25:.3f} {FLAG_Z}
  children [
    Shape {{
      appearance PBRAppearance {{ baseColor 0.95 0.75 0.1 metalness 0.8 roughness 0.3 }}
      geometry Sphere {{ radius 0.35 }}
    }}
  ]
}}"""
    for i in range(FLAG_STRIPS):
        cx = x_hoist + (i + 0.5) * w
        out += f"""
DEF FLAG_STRIP_{i} Transform {{
  translation {cx:.3f} 0 {FLAG_Z}
  children [
    Transform {{
      translation 0 {y_mid:.3f} 0
      children [
        Shape {{
          appearance PBRAppearance {{ baseColor 0.99 0.82 0.09 emissiveColor 0.35 0.28 0.03 roughness 0.8 }}
          geometry Box {{ size {w * 1.1:.3f} {FLAG_H / 2:.3f} 0.04 }}
        }}
      ]
    }}
    Transform {{
      translation 0 {y_bot:.3f} 0
      children [
        Shape {{
          appearance PBRAppearance {{ baseColor 0.0 0.55 0.2 emissiveColor 0.0 0.18 0.06 roughness 0.8 }}
          geometry Box {{ size {w * 1.1:.3f} {FLAG_H / 2:.3f} 0.04 }}
        }}
      ]
    }}
  ]
}}"""
    return out


# ---------------------------------------------------------------------------
# Arboles alrededor del mapa: un anillo por fuera del terreno real y algunos
# en los bordes libres de adentro. Mezcla de arboles de copa redonda (tipo
# almendro/mango) y palmas, comunes en la costa Caribe. Posiciones con semilla
# fija (siempre salen iguales) y sin tocar edificios, torre ni bandera.
# Para cambiar la cantidad: N_ARBOLES_ANILLO y N_ARBOLES_BORDE.
# ---------------------------------------------------------------------------
N_ARBOLES_ANILLO = 46
N_ARBOLES_BORDE = 14
Y_SUELO_EXTERIOR = 2.21        # el plano de suelo (z = -0.05) en coordenadas locales
MAPA_X, MAPA_Z = 62.0, 57.0    # semiancho/semilargo aprox. del terreno real


def _cargar_terreno():
    V, F = [None], []
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "worlds", "meshes", "cad-atlas_3D.obj")
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("v "):
                V.append(tuple(map(float, linea.split()[1:4])))
            elif linea.startswith("f "):
                F.append([int(p.split("/")[0]) for p in linea.split()[1:]])
    return V, F


def _altura_terreno(V, F, x, z):
    for f in F:
        for i in range(1, len(f) - 1):
            a, b, c = V[f[0]], V[f[i]], V[f[i + 1]]
            d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(d) < 1e-12:
                continue
            l1 = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / d
            l2 = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / d
            l3 = 1 - l1 - l2
            if min(l1, l2, l3) >= -1e-9:
                return l1 * a[1] + l2 * b[1] + l3 * c[1]
    return None


_arbol_defs = set()


def _app(nombre, definicion):
    if nombre in _arbol_defs:
        return f"USE {nombre}"
    _arbol_defs.add(nombre)
    return f"DEF {nombre} {definicion}"


def _arbol_redondo(x, y, z, s, verde):
    alto = 1.8 * s
    r = 1.7 * s
    tronco = _app("TRONCO_APP", "PBRAppearance { baseColor 0.35 0.22 0.12 roughness 1 }")
    hoja = _app(f"HOJA_{verde}_APP", "PBRAppearance { baseColor %s roughness 1 }" % (
        ("0.12 0.42 0.14", "0.2 0.5 0.15", "0.08 0.35 0.18")[verde]))
    return f"""
Transform {{
  translation {x:.2f} {y:.2f} {z:.2f}
  children [
    Transform {{
      translation 0 {alto / 2:.2f} 0
      children [ Shape {{ appearance {tronco} geometry Box {{ size {0.45 * s:.2f} {alto:.2f} {0.45 * s:.2f} }} }} ]
    }}
    Transform {{
      translation 0 {alto + r * 0.7:.2f} 0
      children [ Shape {{ appearance {hoja} geometry Sphere {{ radius {r:.2f} subdivision 2 }} }} ]
    }}
    Transform {{
      translation {r * 0.55:.2f} {alto + r * 1.35:.2f} {r * 0.2:.2f}
      children [ Shape {{ appearance {hoja} geometry Sphere {{ radius {r * 0.7:.2f} subdivision 2 }} }} ]
    }}
  ]
}}"""


def _palma(x, y, z, s, giro):
    alto = 7.5 * s
    tronco = _app("TRONCO_PALMA_APP", "PBRAppearance { baseColor 0.45 0.34 0.22 roughness 1 }")
    fronda = _app("FRONDA_APP", "PBRAppearance { baseColor 0.1 0.45 0.12 roughness 1 }")
    frondas = ""
    for k in range(6):
        ang = giro + k * math.pi / 3
        frondas += f"""
        Transform {{
          rotation 0 1 0 {ang:.3f}
          children [
            Transform {{
              translation {1.3 * s:.2f} 0 0
              rotation 0 0 1 -0.45
              children [ Shape {{ appearance {fronda} geometry Box {{ size {2.8 * s:.2f} 0.06 {0.55 * s:.2f} }} }} ]
            }}
          ]
        }}"""
    return f"""
Transform {{
  translation {x:.2f} {y:.2f} {z:.2f}
  children [
    Transform {{
      translation 0 {alto / 2:.2f} 0
      children [ Shape {{ appearance {tronco} geometry Box {{ size {0.35 * s:.2f} {alto:.2f} {0.35 * s:.2f} }} }} ]
    }}
    Transform {{
      translation 0 {alto:.2f} 0
      children [{frondas}
      ]
    }}
  ]
}}"""


def arboles():
    rnd = random.Random(2024)
    V, F = _cargar_terreno()
    libres = [e for e in EDIFICIOS_REALES if e[3] >= 0.8 and e[4] >= 0.8]
    puntos = []

    def valido(x, z, margen_arbol):
        if abs(x + 14) < 12 and abs(z + 3) < 9:        # bandera
            return False
        if math.hypot(x, z) < 8:                        # torre
            return False
        for (cx, cy, cz, dx, dz) in libres:
            if abs(x - cx) < dx / 2 + 3.5 and abs(z - cz) < dz / 2 + 3.5:
                return False
        for (px, pz) in puntos:
            if math.hypot(x - px, z - pz) < margen_arbol:
                return False
        return True

    colocados = []

    def colocar(n, sorteo, y_fn, margen):
        intentos = 0
        hechos = 0
        while hechos < n and intentos < 6000:
            intentos += 1
            x, z = sorteo()
            if not valido(x, z, margen):
                continue
            y = y_fn(x, z)
            if y is None:
                continue
            puntos.append((x, z))
            colocados.append((x, y, z))
            hechos += 1

    def en_anillo():
        while True:
            x = rnd.uniform(-MAPA_X - 14, MAPA_X + 14)
            z = rnd.uniform(-MAPA_Z - 12, MAPA_Z + 12)
            if abs(x) > MAPA_X + 2 or abs(z) > MAPA_Z + 2:
                return x, z

    def en_borde():
        while True:
            x = rnd.uniform(-MAPA_X + 2, MAPA_X - 2)
            z = rnd.uniform(-MAPA_Z + 2, MAPA_Z - 2)
            if abs(x) > MAPA_X - 9 or abs(z) > MAPA_Z - 9:
                return x, z

    colocar(N_ARBOLES_ANILLO, en_anillo, lambda x, z: Y_SUELO_EXTERIOR, 7.0)
    colocar(N_ARBOLES_BORDE, en_borde, lambda x, z: _altura_terreno(V, F, x, z), 7.0)

    out = ""
    for i, (x, y, z) in enumerate(colocados):
        s = rnd.uniform(0.85, 1.3)
        if i % 4 == 3:
            out += _palma(x, y, z, s, rnd.uniform(0, math.pi))
        else:
            out += _arbol_redondo(x, y, z, s, rnd.randrange(3))
    arboles.total = len(colocados)
    arboles.puntos = list(puntos)
    return out


# ---------------------------------------------------------------------------
# Pavimento solo en los espacios vacios entre edificios (calles y patios que
# rodean las construcciones); el resto del terreno queda como tierra. El CAD no
# trae calles, asi que se pavimenta toda celda libre a menos de DIST_PAVIMENTO
# metros de algun edificio. Las celdas contiguas se unen en tiras para no
# generar demasiados nodos. Cada tira sigue la altura del terreno real.
# ---------------------------------------------------------------------------
CELDA = 3.0
DIST_PAVIMENTO = 7.0
ESPESOR_PAV = 0.1


def pavimento(puntos_arboles):
    V, F = _cargar_terreno()
    # indice espacial simple de caras (bins de 6 m) para consultar rapido
    bins = {}
    for f in F:
        xs = [V[i][0] for i in f]
        zs = [V[i][2] for i in f]
        for bx in range(int(min(xs) // 6), int(max(xs) // 6) + 1):
            for bz in range(int(min(zs) // 6), int(max(zs) // 6) + 1):
                bins.setdefault((bx, bz), []).append(f)

    # _altura_terreno recibe (V, F): le pasamos solo las caras del bin
    def altura(x, z, _V=V, _b=bins):
        return _altura_terreno(_V, _b.get((int(x // 6), int(z // 6)), []), x, z)

    libres = [e for e in EDIFICIOS_REALES if e[3] >= 0.8 and e[4] >= 0.8]

    def dist_a_edificios(x, z):
        mejor = 1e9
        for (cx, cy, cz, dx, dz) in libres:
            ax = max(abs(x - cx) - (dx / 2 + 0.9), 0.0)
            az = max(abs(z - cz) - (dz / 2 + 0.9), 0.0)
            mejor = min(mejor, math.hypot(ax, az))
        return mejor

    def pavimentable(x, z):
        d = dist_a_edificios(x, z)
        if d < 1.0 or d > DIST_PAVIMENTO:
            return False
        if abs(x + 14) < 1.5 and abs(z + 3) < 1.5:       # base del asta
            return False
        if math.hypot(x, z) < 2.0:                        # base de la torre
            return False
        for (px, pz) in puntos_arboles:
            if math.hypot(x - px, z - pz) < 2.5:
                return False
        return True

    out = ""
    n_tiras = 0
    nz = int(2 * MAPA_Z // CELDA)
    nx = int(2 * MAPA_X // CELDA)
    for j in range(nz):
        z = -MAPA_Z + (j + 0.5) * CELDA
        run = []                                          # celdas (x, h)
        def volcar():
            nonlocal out, n_tiras
            if not run:
                return
            x0 = run[0][0] - CELDA / 2
            x1 = run[-1][0] + CELDA / 2
            h = sum(r[1] for r in run) / len(run)
            mat = _mat("PAVIMENTO_APP", "0.27 0.27 0.29")
            out += f"""
Transform {{
  translation {(x0 + x1) / 2:.2f} {h + 0.04:.3f} {z:.2f}
  children [ Shape {{ appearance {mat} geometry Box {{ size {x1 - x0:.2f} {ESPESOR_PAV} {CELDA:.2f} }} }} ]
}}"""
            n_tiras += 1
            run.clear()
        for i in range(nx):
            x = -MAPA_X + (i + 0.5) * CELDA
            h = altura(x, z) if pavimentable(x, z) else None
            if h is None:
                volcar()
                continue
            if run and abs(h - run[0][1]) > 0.15:
                volcar()
            run.append((x, h))
        volcar()
    pavimento.total = n_tiras
    return out


def build_world():
    header = """#VRML_SIM R2023b utf8

WorldInfo {
  info [
    "Simulacion: microrred solar de respaldo sobre el mapa real de Cienaga, Magdalena"
    "Edificios sin panel solar: se quedan sin luz en cada corte (situacion actual)"
    "Edificios con panel solar y bateria: mantienen la luz durante el corte (propuesta)"
  ]
  title "Cienaga - Respaldo Solar ante Cortes de Luz"
  basicTimeStep 32
}
Viewpoint {
  orientation -0.336 0.336 0.880 1.6985
  position 0 -95 85
  exposure 1
}
DEF CIELO Background {
  skyColor [
    0.55 0.75 0.95
  ]
}
DEF SOL DirectionalLight {
  direction 0.3 -0.4 -0.9
  intensity 2.5
  ambientIntensity 0.3
  castShadows FALSE
}

DEF GROUND Solid {
  translation 0 0 -0.05
  children [
    Shape {
      appearance PBRAppearance {
        baseColor 0.55 0.65 0.4
        roughness 1
      }
      geometry Plane {
        size 220 180
      }
    }
  ]
  name "suelo_general"
}

DEF MAPA_CIENAGA_REAL Solid {
  translation @@T@@
  rotation @@R@@
  children [
    Shape {
      appearance PBRAppearance {
        baseColor 0.52 0.41 0.29
        roughness 1
      }
      geometry Mesh {
        url [
          "meshes/cad-atlas_3D.obj"
        ]
      }
    }
  ]
  name "mapa_real_cienaga_cad"
}
"""
    header = header.replace("@@T@@", MAPA_TRANSLATION).replace("@@R@@", MAPA_ROTATION)

    _ventana_counter["RSOL"] = 0
    _ventana_counter["RNOS"] = 0
    _fachada_counter[0] = 0
    _fachada_defs.clear()
    _arb = arboles()
    hijos = torre() + bandera() + _arb + pavimento(arboles.puntos)
    n_solar = n_sin = 0
    idx_elegible = 0
    for (cx, cy, cz, dx, dz) in EDIFICIOS_REALES:
        if dx < 0.8 or dz < 0.8:
            continue
        nx, nz = paneles_que_caben(dx, dz)
        puede = nx >= 1 and nz >= 1
        if puede:
            solar = (not COMPARAR_CON_Y_SIN_SOLAR) or (idx_elegible % 2 == 0)
            idx_elegible += 1
        else:
            solar = False
        hijos += edificio(cx, cy, cz, dx, dz, solar)
        if solar:
            n_solar += 1
        else:
            n_sin += 1

    edificios = f"""
DEF EDIFICIOS_MAPA_REAL Solid {{
  translation {MAPA_TRANSLATION}
  rotation {MAPA_ROTATION}
  children [{hijos}
  ]
  name "edificios_mapa_real"
}}
"""
    supervisor = """
DEF GRID_SUPERVISOR Robot {
  translation 0 0 0.5
  children [
    Display {
      name "hud"
      width 480
      height 260
    }
    Display {
      name "cronograma"
      width 620
      height 300
    }
  ]
  name "supervisor_red_electrica"
  controller "grid_supervisor"
  supervisor TRUE
}
"""
    return header + edificios + supervisor, n_solar, n_sin


if __name__ == "__main__":
    text, n_solar, n_sin = build_world()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "worlds", "cienaga_microgrid.wbt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Mundo generado: {out}")
    print(f"Edificios con panel solar: {n_solar}")
    print(f"Edificios sin panel solar: {n_sin}")
    print(f"Arboles: {arboles.total}  |  tiras de pavimento: {pavimento.total}")
    print(f"Ventanas con solar: {_ventana_counter['RSOL']}, sin solar: {_ventana_counter['RNOS']}")
