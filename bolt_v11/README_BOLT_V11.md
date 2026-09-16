# Bolt V11

Bolt V11 es una version modular y agentica de BOLT. La version anterior quedo intacta en `bolt_core.py`.

## Respaldo

Antes de crear esta version se genero una copia en:

`C:\MEL_AI\backups\bolt_v10_20260703_133256`

## Arranque

```powershell
python .\launch_bolt_v11.py
```

Interfaz neural con escucha continua:

```powershell
python .\launch_bolt_neural.py
```

## Modelo local

La ruta recomendada es usar Ollama:

```powershell
ollama serve
ollama pull llama3.1
```

Luego copia `.env.example` como `.env` y deja:

```env
BOLT_MODEL_PROVIDER=ollama
BOLT_LOCAL_MODEL=llama3.1
```

## Gemini opcional

Rota la API key vieja y pon la nueva en `.env`:

```env
BOLT_MODEL_PROVIDER=auto
GEMINI_API_KEY=tu_clave
```

## Herramientas iniciales

- `read_text_file`: leer texto local.
- `write_text_file`: crear o sobrescribir texto local.
- `list_directory`: listar carpetas.
- `make_directory`: crear carpetas.
- `web_search`: buscar en internet.
- `download_file`: descargar archivos.
- `find_and_download_pdfs`: buscar y descargar PDFs directos.
- `create_blender_script`: generar script de Blender.
- `run_blender_script`: ejecutar Blender en background.

## Interfaz Neural

La interfaz neural escucha la palabra de activacion `Bolt` cuando el microfono esta disponible.

Comandos de modo:

- `Bolt, modo constructor`: orientado a modelos 3D, sitios web, scripts, assets y prototipos.
- `Bolt, modo investigador`: orientado a busqueda, PDFs y analisis de fuentes.
- `Bolt, modo sistema`: orientado a archivos, diagnostico y control local.
- `Bolt, modo normal`: vuelve al asistente general.

Atajo:

- `Ctrl+K`: oculta o muestra el teclado de respaldo.

## Siguiente fase

- Extraer texto real de PDFs con `pypdf`.
- Busqueda academica dedicada.
- Memoria vectorial.
- Permisos por riesgo para acciones destructivas.
- Integrar voz y modo centinela desde la V10.
