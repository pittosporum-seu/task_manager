$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Virtual environment not found. Create .venv and install requirements-build.txt first."
}

& $python scripts/create_icon.py

$version = (& $python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name TaskManager `
    --icon app/resources/imgs/app_logo.ico `
    --add-data "app/resources/imgs;app/resources/imgs" `
    main.py

$artifactDir = Join-Path $projectRoot "outputs"
New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

$zipPath = Join-Path $artifactDir "TaskManager-v$version-win64.zip"
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Compress-Archive -Path "dist/TaskManager/*" -DestinationPath $zipPath -Force

Write-Host "Built $zipPath"
