$ErrorActionPreference = "Stop"
$project = $PSScriptRoot
$pythonCandidates = @(
    (Join-Path $project ".venv312\Scripts\python.exe"),
    (Join-Path $project ".venv\Scripts\python.exe")
)
$python = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $python) {
    Write-Host "Python environment not found. Follow the setup steps in README.md first."
    exit 1
}

. (Join-Path $project "ollama_local.ps1")
Start-HintOsOllama
Warm-HintOsOllama

# Replace an older HintOS process from this project's environment so edits load.
$projectPythonPaths = @($pythonCandidates | Where-Object { Test-Path $_ })
$oldHintOsServers = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "python.exe" -and
    $_.CommandLine -match "uvicorn\s+app:app" -and
    $projectPythonPaths -contains $_.ExecutablePath
}
foreach ($server in $oldHintOsServers) {
    Write-Host "Stopping older HintOS server (process $($server.ProcessId))..."
    Stop-Process -Id $server.ProcessId -Force
}

$env:HINTOS_OFFLINE = "1"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
Set-Location $project
$bindHost = $env:HINTOS_BIND_HOST
if ([string]::IsNullOrWhiteSpace($bindHost)) { $bindHost = "127.0.0.1" }
& $python -m uvicorn app:app --host $bindHost --port 8000
