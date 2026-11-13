$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "ReuniteAI setup" -ForegroundColor Cyan
Write-Host "Project folder: $ProjectRoot"

$Python = Get-Command py -ErrorAction SilentlyContinue
if ($Python) { $PythonCmd = "py"; $PythonArgs = @("-3") }
else {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $Python) { throw "Python 3 is not installed. Install Python 3.10+ and reopen PowerShell." }
    $PythonCmd = "python"; $PythonArgs = @()
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $PythonCmd @PythonArgs -m venv .venv
}
$Activate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $Activate)) { throw "Could not find the virtual environment activation script." }
. $Activate

Write-Host "Installing project dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    $Secret = python -c "import secrets; print(secrets.token_urlsafe(48))"
    @(
        "SECRET_KEY=$Secret",
        "DATABASE_URL=sqlite:///reuniteai.sqlite3",
        "COOKIE_SECURE=0",
        "RATELIMIT_STORAGE_URI=memory://"
    ) | Set-Content -Path ".env" -Encoding ascii
    Write-Host "Created a local .env with a randomly generated SECRET_KEY." -ForegroundColor Green
}

Write-Host "Initializing database..." -ForegroundColor Yellow
flask --app run.py init-db
Write-Host "Setup complete. Next run: .\run_windows.ps1" -ForegroundColor Green
Write-Host "Create the first administrator with: flask --app run.py create-admin"
