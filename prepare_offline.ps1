$ErrorActionPreference = "Stop"
$project = $PSScriptRoot
$wheelFolder = Join-Path $project "offline_wheels"

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = "py"
    $pythonArgs = @("-3.12")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = "python"
    $pythonArgs = @()
} else {
    Write-Host "Python is not available. Install Python 3.12, then run this script again."
    exit 1
}

New-Item -ItemType Directory -Force -Path $wheelFolder | Out-Null
Write-Host "Saving Python packages for this Windows computer type to $wheelFolder"
& $pythonCommand @pythonArgs -m pip download --no-cache-dir --only-binary=:all: --dest $wheelFolder -r (Join-Path $project "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Could not download all package wheels. Check your internet connection and Python version."
}
Write-Host "Package cache ready. It is specific to this OS, CPU type, and Python version."
