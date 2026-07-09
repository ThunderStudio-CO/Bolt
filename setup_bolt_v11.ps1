param(
    [string]$Provider = "auto",
    [string]$LocalModel = "llama3.1",
    [string]$GeminiModel = "gemini-2.5-flash"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envPath = Join-Path $root ".env"

if (-not (Test-Path $envPath)) {
    Copy-Item -LiteralPath (Join-Path $root ".env.example") -Destination $envPath
}

$content = Get-Content -LiteralPath $envPath -Raw
$content = $content -replace "BOLT_MODEL_PROVIDER=.*", "BOLT_MODEL_PROVIDER=$Provider"
$content = $content -replace "BOLT_LOCAL_MODEL=.*", "BOLT_LOCAL_MODEL=$LocalModel"
$content = $content -replace "BOLT_GEMINI_MODEL=.*", "BOLT_GEMINI_MODEL=$GeminiModel"
Set-Content -LiteralPath $envPath -Value $content -Encoding UTF8

Write-Host "Bolt V11 configurado en $envPath"
Write-Host "Proveedor: $Provider"
Write-Host "Modelo local: $LocalModel"
Write-Host ""
Write-Host "Para iniciar:"
Write-Host "python .\launch_bolt_v11.py"
