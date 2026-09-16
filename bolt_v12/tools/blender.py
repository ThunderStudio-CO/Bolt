from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import GENERATED_3D_DIR
from .base import Tool, ToolResult


def create_blender_script(prompt: str, script_name: str = "bolt_model.py") -> ToolResult:
    GENERATED_3D_DIR.mkdir(parents=True, exist_ok=True)
    target = GENERATED_3D_DIR / script_name
    code = f'''import bpy

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# Prompt: {prompt}

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

bpy.ops.wm.save_as_mainfile(filepath=str(r"{GENERATED_3D_DIR / 'bolt_generated_model.blend'}"))
'''
    target.write_text(code, encoding="utf-8")
    return ToolResult(True, f"Script de Blender creado: {target}", {"path": str(target)})


def run_blender_script(script_path: str, blender_exe: str = "blender") -> ToolResult:
    target = Path(script_path)
    if not target.exists():
        return ToolResult(False, f"No encontré el script: {target}")
    try:
        completed = subprocess.run(
            [blender_exe, "--background", "--python", str(target)],
            check=False, capture_output=True, text=True, timeout=180,
        )
        ok = completed.returncode == 0
        message = "Blender ejecutó el script." if ok else "Blender devolvió error."
        return ToolResult(ok, message, {"stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]})
    except Exception as exc:
        return ToolResult(False, f"No pude ejecutar Blender: {exc}")


def build_blender_tools() -> list[Tool]:
    return [
        Tool(
            name="create_blender_script",
            description="Crea un script Python de Blender para un modelo 3D.",
            parameters={"prompt": "Descripcion del modelo 3D", "script_name": "Nombre opcional"},
            handler=create_blender_script,
        ),
        Tool(
            name="run_blender_script",
            description="Ejecuta un script de Blender.",
            parameters={"script_path": "Ruta del script", "blender_exe": "Ejecutable opcional"},
            handler=run_blender_script,
        ),
    ]
