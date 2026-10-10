"""
Script opcional para Blender: genera un modelo de casa con mas detalle
(bloque de concreto, techo de zinc inclinado, rejas, puerta y panel
solar) para quien quiera reemplazar manualmente las cajas simples del
mundo Webots por un modelo importado (File > Import 3D Model...).

Uso:
  1. Abrir Blender.
  2. Ir a la pestana "Scripting".
  3. Pegar este script y ejecutar (Run Script).
  4. Exportar el objeto "CasaKennedy" como .obj o .gltf.
  5. En Webots: File > Import 3D Model... y seleccionar el archivo exportado.
"""

import bpy

# Limpiar escena
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Cuerpo principal (bloque de concreto)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.9))
cuerpo = bpy.context.active_object
cuerpo.name = "CasaKennedy"
cuerpo.scale = (2, 2, 1.8)

mat_pared = bpy.data.materials.new(name="ConcretoKennedy")
mat_pared.diffuse_color = (0.68, 0.66, 0.62, 1.0)
cuerpo.data.materials.append(mat_pared)

# Techo de zinc, ligeramente inclinado
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2.0))
techo = bpy.context.active_object
techo.name = "TechoZinc"
techo.scale = (2.15, 2.15, 0.14)
techo.rotation_euler = (0.06, 0, 0)

mat_techo = bpy.data.materials.new(name="ZincKennedy")
mat_techo.diffuse_color = (0.58, 0.58, 0.6, 1.0)
techo.data.materials.append(mat_techo)

# Panel solar (opcional, inclinado sobre el techo)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2.5))
panel = bpy.context.active_object
panel.name = "PanelSolar"
panel.scale = (1.6, 1.6, 0.06)
panel.rotation_euler = (0.35, 0, 0)

mat_panel = bpy.data.materials.new(name="PanelSolarAzul")
mat_panel.diffuse_color = (0.05, 0.08, 0.2, 1.0)
panel.data.materials.append(mat_panel)

# Unir todo en un solo objeto para exportar facilmente
bpy.ops.object.select_all(action='DESELECT')
cuerpo.select_set(True)
techo.select_set(True)
panel.select_set(True)
bpy.context.view_layer.objects.active = cuerpo
bpy.ops.object.join()

print("Modelo 'CasaKennedy' generado. Exportalo como .obj o .gltf desde File > Export.")
