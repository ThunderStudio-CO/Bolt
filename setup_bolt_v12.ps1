# Bolt V12 - Setup
# Ejecuta: .\setup_bolt_v12.ps1

Write-Host "=== Bolt V12 Setup ===" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python no encontrado. Instala Python 3.11+ desde python.org" -ForegroundColor Red
    exit 1
}

# Crear entorno virtual
Write-Host ""
Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
if (-not (Test-Path "venv_v12")) {
    python -m venv venv_v12
}

# Activar entorno
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
.\venv_v12\Scripts\Activate.ps1

# Instalar dependencias
Write-Host ""
Write-Host "Instalando dependencias..." -ForegroundColor Yellow
pip install --upgrade pip
pip install chromadb psutil edge-tts SpeechRecognition pyaudio openai

# Copiar .env si no existe
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "Creando .env desde .env.example.v12..." -ForegroundColor Yellow
    Copy-Item ".env.example.v12" ".env"
    Write-Host "编辑a .env con tu OPENCODE_API_KEY" -ForegroundColor Cyan
    Write-Host "Obtén tu key en: https://opencode.ai/auth" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== Setup completo ===" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar:" -ForegroundColor Cyan
Write-Host "  .\venv_v12\Scripts\Activate.ps1"
Write-Host "  python launch_bolt_v12.py"
Write-Host ""
Write-Host "O con interfaz neural:" -ForegroundColor Cyan
Write-Host "  python launch_bolt_neural_v12.py"
