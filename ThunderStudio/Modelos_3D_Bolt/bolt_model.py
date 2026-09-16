import bpy

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# Prompt: Crea un modelo 3D detallado de un teclado mecánico estilo TKL (tenkeyless). Debe incluir: 1) Una base rectangular con esquinas redondeadas y un ligero bisel superior, color negro oscuro. 2) Una placa interior gris oscuro ligeramente elevada. 3) Keycaps con perfil OEM: cada keycap debe ser una forma de prisma con la parte superior cóncava (usar un cubo con bevel y leve escala en la parte superior), distribuidos en filas escalonadas (staggered layout): fila QWERTY con offset de 0.25u, fila ASDF con 0.5u de offset, fila ZXCV con 0.75u, fila espaciadora más ancha. Usar colores: teclas alfanuméricas en gris claro, teclas modificadoras (Shift, Ctrl, Alt, Enter, Backspace) en gris oscuro, y teclas WASD resaltadas en rojo. 4) Una barra espaciadora larga. 5) Detalles como tornillos visibles en las esquinas inferiores y un cable USB que sale de la parte trasera. Usar objetos separados para cada pieza (base, placa, keycaps) para facilitar la edición posterior. Escala aproximada: cada tecla de 1u debe medir 18mm x 18mm.

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
