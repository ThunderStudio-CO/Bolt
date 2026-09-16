import bpy
import bmesh
from math import radians

# Limpiar escena
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

U = 0.018  # 1u = 18mm en metros

# ---------- Materiales ----------
def make_mat(name, color, roughness=0.4, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

mat_case = make_mat("Case_Black", (0.02, 0.02, 0.02, 1), 0.6)
mat_plate = make_mat("Plate_Grey", (0.18, 0.18, 0.2, 1), 0.5, 0.3)
mat_alpha = make_mat("Keycap_Alpha", (0.78, 0.78, 0.78, 1), 0.35)
mat_mod = make_mat("Keycap_Mod", (0.32, 0.32, 0.35, 1), 0.35)
mat_wasd = make_mat("Keycap_WASD", (0.85, 0.12, 0.12, 1), 0.35)
mat_space = make_mat("Keycap_Space", (0.45, 0.45, 0.5, 1), 0.3)
mat_screw = make_mat("Screw_Metal", (0.7, 0.7, 0.7, 1), 0.2, 1.0)
mat_cable = make_mat("Cable_Black", (0.02, 0.02, 0.02, 1), 0.8)

# ---------- Base ----------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
base = bpy.context.object
base.name = "TKL_Base"
base.scale = (U * 36.5, U * 13.5, U * 1.2)
base.location.z = U * 0.6
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bevel = base.modifiers.new("Bevel", "BEVEL")
bevel.width = U * 0.3
bevel.segments = 4
bevel.limit_method = "ANGLE"
bevel.angle_limit = radians(30)
base.data.materials.append(mat_case)

# ---------- Placa ----------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
plate = bpy.context.object
plate.name = "TKL_Plate"
plate.scale = (U * 35.5, U * 12.5, U * 0.4)
plate.location.z = U * 1.4
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bevel2 = plate.modifiers.new("Bevel", "BEVEL")
bevel2.width = U * 0.15
bevel2.segments = 3
bevel2.limit_method = "ANGLE"
plate.data.materials.append(mat_plate)

# ---------- Keycap builder ----------
def make_keycap(x, y, width_u=1.0, ktype="alpha"):
    w = U * width_u
    d = U
    h = U * 0.75
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, U * 1.4 + h / 2))
    obj = bpy.context.object
    obj.scale = (w, d, h)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Leve escala de la cara superior (perfil OEM)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    top_verts = []
    for f in bm.faces:
        if abs(f.normal.z) > 0.9:
            for v in f.verts:
                if v not in top_verts:
                    top_verts.append(v)
    bmesh.ops.scale(bm, vec=(0.88, 0.88, 1.0), verts=top_verts)
    bm.to_mesh(obj.data)
    bm.free()

    bev = obj.modifiers.new("Bevel", "BEVEL")
    bev.width = U * 0.1
    bev.segments = 3
    bev.limit_method = "ANGLE"
    bev.angle_limit = radians(50)

    if ktype == "alpha":
        obj.data.materials.append(mat_alpha)
    elif ktype == "mod":
        obj.data.materials.append(mat_mod)
    elif ktype == "wasd":
        obj.data.materials.append(mat_wasd)
    elif ktype == "space":
        obj.data.materials.append(mat_space)
    return obj

# ---------- Layout TKL ----------
base_x = -U * 17.0
base_y = -U * 6.5

# Filas de abajo hacia arriba: (offset_x, [(ancho, tipo), ...])
rows_principal = [
    (0, [
        (1.25, "mod"), (1.25, "mod"), (1.25, "mod"), (6.25, "space"),
        (1.25, "mod"), (1.25, "mod"), (1.25, "mod"), (1.25, "mod")
    ]),
    (0.75, [
        (2.25, "mod"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (2.75, "mod")
    ]),
    (0.5, [
        (1.75, "mod"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (2.25, "mod")
    ]),
    (0.25, [
        (1.5, "mod"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (1.5, "mod")
    ]),
    (0, [
        (1, "mod"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (1, "alpha"), (2, "mod")
    ]),
    (0, [
        (1, "mod"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"),
        (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha"), (1, "alpha")
    ]),
]

for i, (offset, keys) in enumerate(rows_principal):
    y = base_y + i * U
    x = base_x + offset * U
    alpha_count = 0
    for (w, kt) in keys:
        actual_type = kt
        if kt == "alpha":
            alpha_count += 1
            # QWERTY (i=3): W es el 2º alpha
            if i == 3 and alpha_count == 2:
                actual_type = "wasd"
            # ASDF (i=2): A=2º, S=3º, D=4º
            if i == 2 and alpha_count in (2, 3, 4):
                actual_type = "wasd"
        make_keycap(x + w * U / 2, y, w, actual_type)
        x += w * U

# ---------- Bloque de navegación TKL ----------
nav_x0 = base_x + 17.5 * U
nav_y0 = base_y + 5 * U
for j in range(3):
    make_keycap(nav_x0 + j * U + U / 2, nav_y0, 1, "mod")       # Insert / Home / PgUp
    make_keycap(nav_x0 + j * U + U / 2, nav_y0 - U, 1, "mod")   # Delete / End / PgDn

# Flechas (T invertida) en la fila de la espaciadora
arrows_x = nav_x0
arrows_y = base_y
make_keycap(arrows_x + U / 2, arrows_y + U, 1, "mod")   # Up
make_keycap(arrows_x, arrows_y, 1, "mod")               # Left
make_keycap(arrows_x + U, arrows_y, 1, "mod")           # Down
make_keycap(arrows_x + 2 * U, arrows_y, 1, "mod")       # Right

# ---------- Tornillos ----------
for sx in (-1, 1):
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=U * 0.35, depth=U * 0.5, location=(sx * U * 17.0, sy * U * 6.0, U * 0.1))
        screw = bpy.context.object
        screw.name = "Screw"
        screw.data.materials.append(mat_screw)

# ---------- Cable USB ----------
bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=False, location=(0, -U * 7.2, U * 0.6))
cable = bpy.context.object
cable.name = "USB_Cable"
curve = cable.data
curve.bevel_depth = U * 0.12
curve.fill_mode = "FULL"
curve.render_resolution_u = 12
pts = curve.splines[0].bezier_points
pts[0].co = (0, 0, 0)
pts[0].handle_right_type = "AUTO"
pts[1].co = (U * 5, U * 1.5, -U * 2)
pts[1].handle_left_type = "AUTO"
cable.data.materials.append(mat_cable)

# ---------- Aplicar bevels de keycaps para edición directa ----------
for obj in bpy.data.objects:
    if "Bevel" in obj.modifiers:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier="Bevel")
        except RuntimeError:
            pass
        obj.select_set(False)

bpy.ops.wm.save_as_mainfile(filepath=r"C:\MEL_AI\ThunderStudio\Modelos_3D_Bolt\bolt_teclado_tkl.blend")
print("Teclado TKL generado correctamente")