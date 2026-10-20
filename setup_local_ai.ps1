$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "ollama_local.ps1")
Start-HintOsOllama

$model = $env:HINTOS_LOCAL_MODEL
if ([string]::IsNullOrWhiteSpace($model)) {
    $model = "qwen3.5:2b"
    $env:HINTOS_LOCAL_MODEL = $model
}

Write-Host "Downloading the local HintOS tutor model: $model"
& $script:HintOsOllamaExe pull $model
if ($LASTEXITCODE -ne 0) {
    throw "Ollama could not download $model into $script:HintOsOllamaStore. Check the connection and free space on this drive."
}

Write-Host "The model is stored with this project at $script:HintOsOllamaStore. HintOS can use it offline after this download."
