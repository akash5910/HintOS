$ErrorActionPreference = "Stop"

$script:HintOsProject = $PSScriptRoot
$script:HintOsOllamaStore = Join-Path $PSScriptRoot "ollama\Models\models"
if (-not (Test-Path (Join-Path $script:HintOsOllamaStore "blobs"))) {
    $script:HintOsOllamaStore = Join-Path $PSScriptRoot "ollama\models"
}
New-Item -ItemType Directory -Force -Path $script:HintOsOllamaStore | Out-Null

# Give this project its own Ollama service and model directory. This avoids
# accidentally using Ollama's default per-user store on the C: drive.
$env:OLLAMA_MODELS = $script:HintOsOllamaStore
$env:OLLAMA_HOST = "127.0.0.1:11435"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11435"
$env:OLLAMA_NO_CLOUD = "1"
$env:NO_PROXY = "127.0.0.1,localhost"
$env:no_proxy = $env:NO_PROXY
$projectCache = Join-Path $PSScriptRoot ".cache"
$env:HF_HOME = Join-Path $projectCache "huggingface"
$env:HF_HUB_CACHE = Join-Path $env:HF_HOME "hub"
$env:TRANSFORMERS_CACHE = $env:HF_HUB_CACHE

$bundledOllama = Join-Path $PSScriptRoot "ollama\ollama.exe"
if (Test-Path $bundledOllama) {
    $script:HintOsOllamaExe = $bundledOllama
} else {
    $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollamaCommand) {
        throw "Ollama was not found. Install Ollama or include the project's ollama folder."
    }
    $script:HintOsOllamaExe = $ollamaCommand.Source
}

function Test-HintOsOllama {
    try {
        $null = Invoke-RestMethod -Uri "$env:OLLAMA_BASE_URL/api/tags" -TimeoutSec 1
        return $true
    } catch {
        return $false
    }
}

function Start-HintOsOllama {
    if (Test-HintOsOllama) { return }

    Write-Host "Starting HintOS Ollama with its model store at $script:HintOsOllamaStore"
    Start-Process -FilePath $script:HintOsOllamaExe -ArgumentList "serve" `
        -WorkingDirectory (Split-Path $script:HintOsOllamaExe -Parent) -WindowStyle Hidden | Out-Null

    $deadline = (Get-Date).AddSeconds(45)
    while ((Get-Date) -lt $deadline) {
        if (Test-HintOsOllama) { return }
        Start-Sleep -Milliseconds 500
    }
    throw "HintOS could not start its local Ollama service on 127.0.0.1:11435. Check whether that port is in use."
}

function Warm-HintOsOllama {
    $model = $env:HINTOS_LOCAL_MODEL
    if ([string]::IsNullOrWhiteSpace($model)) { $model = "qwen3.5:2b" }
    try {
        $tags = Invoke-RestMethod -Uri "$env:OLLAMA_BASE_URL/api/tags" -TimeoutSec 2
        $available = @($tags.models | ForEach-Object { $_.name }) -contains $model
        if (-not $available) { return }

        Write-Host "Loading $model into memory for quicker first replies..."
        $body = @{ model = $model; keep_alive = "30m" } | ConvertTo-Json -Depth 4
        $null = Invoke-RestMethod -Uri "$env:OLLAMA_BASE_URL/api/chat" -Method Post `
            -ContentType "application/json" -Body $body -TimeoutSec 240
        Write-Host "The local tutor model is ready."
    } catch {
        Write-Warning "Model warm-up did not complete. HintOS will still start, but its first AI answer may take longer."
    }
}
