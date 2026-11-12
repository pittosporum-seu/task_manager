$ErrorActionPreference = "Stop"
$source = Join-Path $PSScriptRoot "..\dist\TaskManager"
if (Test-Path (Join-Path $PSScriptRoot "TaskManager.exe")) { $source = $PSScriptRoot }
if (-not (Test-Path (Join-Path $source "TaskManager.exe"))) {
    throw "Build first: scripts/build_exe.ps1"
}
if (Get-Process TaskManager -ErrorAction SilentlyContinue) {
    throw "Quit MyTask from the tray before installing."
}
$destination = Join-Path $env:LOCALAPPDATA "Programs\MyTask"
New-Item -ItemType Directory -Force $destination | Out-Null
Copy-Item -Path "$source\*" -Destination $destination -Recurse -Force
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\MyTask.lnk"))
$shortcut.TargetPath = Join-Path $destination "TaskManager.exe"
$shortcut.WorkingDirectory = $destination
$shortcut.Save()
$cliPath = Join-Path $destination "cli"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($cliPath -notin ($userPath -split ';')) {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$cliPath", "User")
}
Write-Host "Installed: $destination"
