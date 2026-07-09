import bpy
from mathutils import Vector

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# Prompt original de Miguel/BOLT:
# Crea un script de Python para Blender que genere un modelo 3D básico de un mouse de computadora. Usa una esfera escalada para el cuerpo principal y añade dos cubos aplanados para los botones izquierdo y derecho en la parte superior.

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
body = bpy.context.object
body.name = "Bolt_Generated_Blockout"
body.scale = (1.8, 0.8, 0.45)

bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(0, 0, 1.65))
dome = bpy.context.object
dome.name = "Bolt_Generated_Dome"
dome.scale = (0.85, 0.85, 0.35)

mat_body = bpy.data.materials.new("Bolt cyan metal")
mat_body.diffuse_color = (0.0, 0.75, 1.0, 1.0)
body.data.materials.append(mat_body)

mat_dome = bpy.data.materials.new("Bolt dark glass")
mat_dome.diffuse_color = (0.02, 0.03, 0.05, 0.75)
dome.data.materials.append(mat_dome)

bpy.ops.object.light_add(type="AREA", location=(0, -4, 6))
light = bpy.context.object
light.name = "Bolt_Key_Light"
light.data.energy = 400
light.data.size = 5

bpy.ops.wm.save_as_mainfile(filepath=str(r"C:\MEL_AI\ThunderStudio\Modelos_3D_Bolt\bolt_generated_model.blend"))
