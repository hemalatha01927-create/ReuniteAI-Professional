$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$Activate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $Activate)) {
    throw "Virtual environment not found. Run .\setup_windows.ps1 first."
}
. $Activate
python run.py
