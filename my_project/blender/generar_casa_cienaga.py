"""
OPCIONAL - Solo si quieres casas mas detalladas que las cajas simples de Webots.

Como usarlo:
1. Abre Blender (gratis, blender.org).
2. Ve a la pestaña "Scripting" (arriba).
3. Abre este archivo con "Open" o pega su contenido en el editor de texto.
4. Presiona "Run Script" (el boton de play, o Alt+P).
5. Se genera una casa caribena sencilla (paredes + techo a dos aguas + panel solar).
6. Selecciona el objeto generado, ve a File > Export > glTF 2.0 (.glb)
   o Wavefront (.obj), y guarda el archivo.
7. En Webots: click derecho en el arbol de la escena > Add > Shape > o usa
   "Import 3D Model" (menu File > Import 3D Model...) y selecciona el .glb/.obj.
   Webots lo convertira automaticamente a un nodo Shape/Mesh que puedes
   copiar dentro de cada DEF HOUSE_XXX del archivo cienaga_microgrid.wbt,
   reemplazando la caja simple si quieres mas realismo visual.

Nota: esto es un extra visual. La simulacion (cortes de luz, respaldo solar,
bateria) funciona igual sin este paso, porque esa logica esta en el
controlador Python (grid_supervisor.py), no en la forma de las casas.
"""

import bpy


def limpiar_escena():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def crear_casa_caribena(nombre="Casa_Cienaga", con_panel_solar=True):
    # Cuerpo de la casa
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    cuerpo = bpy.context.object
    cuerpo.name = nombre
    cuerpo.scale = (1.0, 1.0, 1.0)

    mat_pared = bpy.data.materials.new(name="Pared")
    mat_pared.diffuse_color = (0.85, 0.65, 0.45, 1.0)  # tono caribeno calido
    cuerpo.data.materials.append(mat_pared)

    # Techo a dos aguas (prisma simple hecho con un cubo escalado y rotado)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.6, depth=1.0,
                                     location=(0, 0, 2.5), rotation=(0, 0, 0.785398))
    techo = bpy.context.object
    techo.name = f"{nombre}_techo"
    techo.scale = (1.0, 0.6, 0.5)
    mat_techo = bpy.data.materials.new(name="Techo")
    mat_techo.diffuse_color = (0.35, 0.15, 0.1, 1.0)
    techo.data.materials.append(mat_techo)

    if con_panel_solar:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, 2.7))
        panel = bpy.context.object
        panel.name = f"{nombre}_panel_solar"
        panel.scale = (0.7, 0.7, 0.03)
        mat_panel = bpy.data.materials.new(name="PanelSolar")
        mat_panel.diffuse_color = (0.05, 0.08, 0.25, 1.0)
        panel.data.materials.append(mat_panel)

    return cuerpo


if __name__ == "__main__":
    limpiar_escena()
    crear_casa_caribena()
    print("Casa generada. Ahora exporta con File > Export > glTF 2.0 (.glb)")
