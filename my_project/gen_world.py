"""
Generador del archivo .wbt para la simulacion de microrred solar sobre el
mapa real de Cienaga (levantamiento CAD aportado por el usuario).

Se ejecuta cada vez que se quiera regenerar el mundo:
    python3 gen_world.py
"""
import os

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

    color = "0.72 0.7 0.66" if not solar else "0.75 0.74 0.7"
    return f"""
Transform {{
  translation {cx:.3f} {base:.3f} {cz:.3f}
  children [
    Shape {{
      appearance PBRAppearance {{
        baseColor {color}
        roughness 0.92
      }}
      geometry Box {{
        size {dx:.3f} {ALTURA_EDIFICIO_REAL} {dz:.3f}
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
Background {
  skyColor [
    0.55 0.75 0.95
  ]
}
DirectionalLight {
  direction 0.3 -0.4 -0.9
  intensity 2.5
  castShadows TRUE
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
        baseColor 0.85 0.85 0.85
        roughness 0.9
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
    hijos = torre()
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
    print(f"Ventanas con solar: {_ventana_counter['RSOL']}, sin solar: {_ventana_counter['RNOS']}")
