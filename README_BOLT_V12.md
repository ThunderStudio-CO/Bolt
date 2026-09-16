# Bolt V12 - Asistente Agentic Inteligente

Bolt V12 es un asistente agentic de nivel J.A.R.V.I.S./T.A.R.D.I.S. potenciado por Big Pickle (OpenCode Zen).

## Arquitectura

```
bolt_v12/
├── agent/          # Agente con planificación y chain-of-thought
├── memory/         # Memoria episódica + vectorial (ChromaDB)
├── tools/          # 35+ herramientas
│   ├── files.py    # Archivos y carpetas
│   ├── web.py      # Búsqueda y descarga
│   ├── system.py   # Apps, shell, comandos
│   ├── code_executor.py  # Ejecución Python sandbox
│   ├── git_tools.py      # Git completo
│   ├── monitor.py        # Monitoreo del sistema
│   ├── blender.py        # 3D
│   └── webdev.py         # Sitios web
├── proactive/      # Monitoreo, alertas, tareas en background
├── voice/          # Voz TTS + wake word
└── ui/             # Neural Canvas animado
```

## Arranque

Interfaz de texto:
```powershell
python launch_bolt_v12.py
```

Interfaz neural con voz:
```powershell
python launch_bolt_neural_v12.py
```

## Configuración

1. Copia `.env.example.v12` como `.env` y pon tu API key
2. Obtén tu API key de Big Pickle en https://opencode.ai/auth
3. Pon `OPENCODE_API_KEY=tu_clave` en `.env`

## Modelo Big Pickle

- Gratuito por tiempo limitado
- 200K tokens de contexto
- 32K tokens de output
- Soporte nativo para tool calling
- Razonamiento avanzado (chain-of-thought)

## Herramientas Disponibles

### Archivos
- `read_text_file`, `write_text_file`, `append_text_file`
- `list_directory`, `make_directory`, `delete_file`
- `search_files`, `get_file_info`

### Web
- `web_search`, `fetch_webpage`
- `download_file`, `find_and_download_pdfs`

### Sistema
- `open_app`, `open_path`, `reveal_path`, `open_url`
- `run_shell_command`

### Código
- `execute_python_code` (sandbox)
- `execute_in_terminal`
- `install_package`

### Git
- `git_status`, `git_log`, `git_diff`
- `git_commit`, `git_push`, `git_pull`
- `git_clone`, `git_branch_list`, `git_checkout`

### Monitoreo
- `get_system_info`, `get_running_processes`
- `get_disk_usage`, `get_network_info`
- `monitor_alerts`

### 3D y Web
- `create_blender_script`, `run_blender_script`
- `create_static_website`

## Modos

- **normal**: Asistente general
- **constructor**: Creación de modelos 3D, sitios web, scripts
- **investigador**: Búsqueda, análisis, PDFs
- **sistema**: Control local, terminal, git
- **creativo**: Ideas innovadoras y diseños

## Memoria

- **Episódica**: Conversaciones completas (JSONL)
- **Vectorial**: Búsqueda semántica (ChromaDB)
- **Conocimiento**: Hechos, preferencias, proyectos

## Comandos de Voz

- `Bolt, modo constructor`: Activa modo constructor
- `Bolt, abre vscode`: Abre VS Code
- `Bolt, status del sistema`: Info del sistema
- `Bolt, crea sitio web sobre...`: Crea un sitio

## Seguridad

- Herramientas peligrosas marcadas con `[REQUIERE CONFIRMACION]`
- Ejecución de código en sandbox aislado
- Monitoreo proactivo con alertas
