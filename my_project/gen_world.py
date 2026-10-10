"""
Generador del archivo .wbt para la simulacion de microrred solar en el
barrio Kennedy, Cienaga. Se ejecuta UNA sola vez en este entorno para
producir el mundo Webots.
"""

# El modelo CAD real (cad-atlas_3D.obj) no trae etiquetas de barrios o
# calles, asi que no hay forma de saber en que manzana exacta del mapa
# queda Kennedy. Por eso el conjunto de casas se ubica en un lote
# adyacente al mapa real (desplazado KENNEDY_X_OFFSET en X), separado
# para que no se encime con los edificios reales importados.
KENNEDY_X_OFFSET = 100

BARRIOS = [
    # (nombre_zona, prefijo_def, centro_x, centro_y, tiene_solar)
    ("Kennedy - Zona sin panel solar (Norte)", "NA", -9 + KENNEDY_X_OFFSET,  6, False),
    ("Kennedy - Zona sin panel solar (Sur)",   "SA", -9 + KENNEDY_X_OFFSET, -6, False),
    ("Kennedy - Zona con panel solar (Norte)", "NB",  9 + KENNEDY_X_OFFSET,  6, True),
    ("Kennedy - Zona con panel solar (Sur)",   "SB",  9 + KENNEDY_X_OFFSET, -6, True),
]

HOUSE_OFFSETS = [
    (dx, dy)
    for dy in (-2.6, 0, 2.6)
    for dx in (-2.6, 0, 2.6)
]  # conjunto de 3x3 = 9 casas por bloque, bien juntas como un conjunto residencial

# Paleta inspirada en el barrio Kennedy: casas humildes de un piso,
# bloque de concreto a la vista o pintado en tonos sencillos (no el
# estilo colonial vistoso del centro historico). Cada tupla es
# (color_pared, color_techo, tipo_techo) donde tipo_techo es "losa" (placa
# de concreto plana) o "zinc" (lamina con leve inclinacion).
PALETA = [
    ("0.68 0.66 0.62", "0.78 0.78 0.75", "losa"),   # bloque de concreto sin pintar + placa
    ("0.55 0.68 0.78", "0.58 0.58 0.6",  "zinc"),    # celeste desgastado + zinc
    ("0.8 0.6 0.55",   "0.78 0.78 0.75", "losa"),    # salmon + placa
    ("0.63 0.72 0.6",  "0.58 0.58 0.6",  "zinc"),    # verde palido + zinc
    ("0.7 0.65 0.5",   "0.58 0.58 0.6",  "zinc"),    # beige + zinc
    ("0.68 0.66 0.62", "0.58 0.58 0.6",  "zinc"),    # bloque de concreto sin pintar + zinc
]

_color_counter = 0


def house_block(def_id, x, y, tiene_solar, orientacion=-1):
    global _color_counter
    color_pared, color_techo, tipo_techo = PALETA[_color_counter % len(PALETA)]
    _color_counter += 1

    # orientacion: -1 -> puerta/ventana miran hacia -y (barrios al norte)
    #               1 -> puerta/ventana miran hacia +y (barrios al sur)
    frente_y = -1.01 * orientacion
    reja_y = -1.03 * orientacion
    rot_x = 1.5708 if orientacion < 0 else -1.5708

    inclinacion_techo = 0.0 if tipo_techo == "losa" else 0.06

    barras = ""
    for i in range(4):
        bx = -0.2 + i * 0.13
        barras += f"""
        Transform {{
          translation {bx:.2f} {reja_y} 0.15
          rotation 1 0 0 {rot_x}
          children [
            Shape {{
              appearance PBRAppearance {{
                baseColor 0.15 0.15 0.15
                metalness 0.6
                roughness 0.5
              }}
              geometry Box {{
                size 0.03 0.6 0.03
              }}
            }}
          ]
        }}"""

    panel = ""
    if tiene_solar:
        panel = f"""
        Transform {{
          translation 0 0 1.25
          rotation 1 0 0 0.35
          children [
            Shape {{
              appearance PBRAppearance {{
                baseColor 0.05 0.08 0.2
                metalness 0.6
                roughness 0.3
              }}
              geometry Box {{
                size 1.6 1.6 0.06
              }}
            }}
          ]
        }}"""
    return f"""
DEF HOUSE_{def_id} Solid {{
  translation {x} {y} 0.9
  children [
    Shape {{
      appearance PBRAppearance {{
        baseColor {color_pared}
        roughness 0.95
      }}
      geometry Box {{
        size 2 2 1.8
      }}
    }}
    Transform {{
      translation 0 0 1.0
      rotation 1 0 0 {inclinacion_techo}
      children [
        Shape {{
          appearance PBRAppearance {{
            baseColor {color_techo}
            metalness 0.25
            roughness 0.65
          }}
          geometry Box {{
            size 2.15 2.15 0.14
          }}
        }}
      ]
    }}
    Transform {{
      translation 0.5 {frente_y} 0.15
      rotation 1 0 0 {rot_x}
      children [
        DEF WIN_{def_id} Shape {{
          appearance DEF WIN_{def_id}_APP PBRAppearance {{
            baseColor 0.85 0.87 0.85
            emissiveColor 0 0 0
            roughness 0.4
          }}
          geometry Box {{
            size 0.55 0.55 0.05
          }}
        }}
      ]
    }}{barras}
    Transform {{
      translation -0.5 {frente_y} -0.4
      rotation 1 0 0 {rot_x}
      children [
        Shape {{
          appearance PBRAppearance {{
            baseColor 0.28 0.3 0.3
            metalness 0.4
            roughness 0.6
          }}
          geometry Box {{
            size 0.55 1.0 0.05
          }}
        }}
      ]
    }}{panel}
  ]
  name "casa_{def_id}"
  boundingObject Box {{
    size 2 2 1.8
  }}
}}
"""


def barrio_sign_color(tiene_solar):
    return "0.1 0.6 0.9" if tiene_solar else "0.6 0.15 0.15"


def barrio_block(nombre, prefijo, cx, cy, tiene_solar):
    houses = ""
    house_defs = []
    orientacion = -1 if cy > 0 else 1  # las casas miran hacia la calle central
    for i, (dx, dy) in enumerate(HOUSE_OFFSETS, start=1):
        def_id = f"{prefijo}{i}"
        house_defs.append(def_id)
        houses += house_block(def_id, cx + dx, cy + dy, tiene_solar, orientacion)

    sign_color = barrio_sign_color(tiene_solar)
    sign = f"""
DEF SIGN_{prefijo} Solid {{
  translation {cx} {cy + orientacion * 4.5} 1.2
  children [
    Shape {{
      appearance PBRAppearance {{ baseColor 0.4 0.4 0.4 }}
      geometry Cylinder {{ height 2.4 radius 0.08 }}
    }}
    Transform {{
      translation 0 0 1.3
      children [
        Shape {{
          appearance PBRAppearance {{ baseColor {sign_color} }}
          geometry Box {{ size 1.4 0.08 0.6 }}
        }}
      ]
    }}
  ]
  name "letrero_{prefijo}"
}}
"""
    return houses + sign, house_defs


def tower_block():
    return f"""
DEF TOWER Solid {{
  translation {KENNEDY_X_OFFSET} 0 0
  children [
    Shape {{
      appearance PBRAppearance {{ baseColor 0.3 0.3 0.3 metalness 0.7 roughness 0.4 }}
      geometry Cylinder {{ height 9 radius 0.35 }}
    }}
    Transform {{
      translation 0 0 4.6
      children [
        Shape {{
          appearance PBRAppearance {{ baseColor 0.3 0.3 0.3 metalness 0.7 roughness 0.4 }}
          geometry Box {{ size 3.2 0.2 0.2 }}
        }}
      ]
    }}
    Transform {{
      translation 0 0 5.1
      children [
        DEF TOWER_LIGHT Shape {{
          appearance DEF TOWER_LIGHT_APP PBRAppearance {{
            baseColor 0.2 0.2 0.2
            emissiveColor 0 0 0
          }}
          geometry Sphere {{ radius 0.25 }}
        }}
      ]
    }}
  ]
  name "torre_electrica_inestable"
  boundingObject Cylinder {{ height 9 radius 0.35 }}
}}
"""


def build_world():
    global _color_counter
    _color_counter = 0
    header = """#VRML_SIM R2023b utf8

WorldInfo {
  info [
    "Simulacion: microrred solar de respaldo para el barrio Kennedy - Cienaga, Magdalena"
    "Zona sin panel solar: se queda sin luz en cada corte (situacion actual)"
    "Zona con panel solar de respaldo: mantiene la luz durante el corte (propuesta)"
  ]
  title "Barrio Kennedy - Respaldo Solar ante Cortes de Luz"
  basicTimeStep 32
  contactProperties [
  ]
}
Viewpoint {
  orientation -0.2 0.05 0.98 1.45
  position @@OFFX@@ -42 27
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
PointLight {
  location 0 0 6
  intensity 2
  radius 15
  attenuation 0 0 1
}

DEF GROUND Solid {
  translation 25 0 0
  children [
    Shape {
      appearance PBRAppearance {
        baseColor 0.55 0.65 0.4
        roughness 1
      }
      geometry Plane {
        size 260 140
      }
    }
  ]
  name "suelo_general"
}

DEF MAPA_CIENAGA_REAL Solid {
  translation 0 0 -2.26
  rotation 1 0 0 1.5708
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

DEF CALLE Solid {
  translation @@OFFX@@ 0 0.02
  children [
    Shape {
      appearance PBRAppearance {
        baseColor 0.25 0.25 0.25
        roughness 0.9
      }
      geometry Plane {
        size 4 32
      }
    }
    Transform {
      children [
        Shape {
          appearance PBRAppearance {
            baseColor 0.25 0.25 0.25
            roughness 0.9
          }
          geometry Plane {
            size 40 4
          }
        }
      ]
    }
  ]
  name "calle_kennedy"
}
"""
    header = header.replace("@@OFFX@@", str(KENNEDY_X_OFFSET))

    body = tower_block()
    barrio_info = []
    for nombre, prefijo, cx, cy, tiene_solar in BARRIOS:
        block, defs = barrio_block(nombre, prefijo, cx, cy, tiene_solar)
        body += block
        barrio_info.append((nombre, prefijo, defs, tiene_solar))

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

    world_text = header + body + supervisor
    return world_text, barrio_info


if __name__ == "__main__":
    text, info = build_world()
    with open("/home/claude/cienaga_solar_sim/worlds/cienaga_microgrid.wbt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Mundo generado. Barrios:")
    for nombre, prefijo, defs, solar in info:
        print(f"  {nombre} ({prefijo}) solar={solar} casas={defs}")
