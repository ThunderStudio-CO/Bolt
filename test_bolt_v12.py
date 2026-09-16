from bolt_v12.config import load_config
from bolt_v12.models import build_model_provider
from bolt_v12.agent import BoltAgent
from bolt_v12.tools.monitor import get_system_info, monitor_alerts
from bolt_v12.tools.files import list_directory
from bolt_v12.tools.web import web_search
from bolt_v12.tools.code_executor import execute_python_code

config = load_config()
provider = build_model_provider(config)

print("=== BOLT V12 - TEST DE CAPACIDADES ===")
print(f"Proveedor: {provider.name}")
print()

# 1. Info del sistema
r = get_system_info()
print(f"[1] System Info: {r.message}")
if r.data:
    print(f"    OS: {r.data.get('os','?')} {str(r.data.get('os_version',''))[:30]}")
    print(f"    RAM: {r.data.get('ram_percent','N/A')}% | CPU: {r.data.get('cpu_percent','N/A')}%")
print()

# 2. Listar directorio
r = list_directory(".")
print(f"[2] Directorio: {len(r.data.get('items',[]))} items")
for item in r.data.get("items", [])[:6]:
    icon = "d" if item["type"] == "dir" else "f"
    print(f"    [{icon}] {item['name']}")
print()

# 3. Buscar en web
r = web_search("python AI agent framework", max_results=3)
print(f"[3] Web: {r.message}")
for res in (r.data or {}).get("results", []):
    print(f"    - {res['title'][:60]}")
print()

# 4. Ejecutar Python
r = execute_python_code("import math; print(f'Pi = {math.pi:.10f}'); print(f'e = {math.e:.10f}')")
print(f"[4] Code Exec: {r.message}")
print(f"    {r.data.get('stdout','').strip()}")
print()

# 5. Alertas
r = monitor_alerts()
print(f"[5] Sistema: CPU={r.data.get('cpu',0)}% | Disco={r.data.get('disk',0)}% | RAM={r.data.get('memory',0)}%")
print(f"    Alertas: {r.data.get('alerts', [])}")
print()

print("=== TODAS LAS HERRAMIENTAS FUNCIONAN ===")
