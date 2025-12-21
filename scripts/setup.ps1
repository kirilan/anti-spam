# PowerShell setup script for Windows
# Run with: .\scripts\setup.ps1

Write-Host "Setting up Data Deletion Assistant..." -ForegroundColor Green

# Check prerequisites
$errors = @()

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    $errors += "Python is not installed. Please install Python 3.11 or 3.12 from python.org"
}
else {
    $pyVersion = python --version 2>&1
    if ($pyVersion -notmatch "3\.(11|12)") {
        Write-Host "Warning: Python version should be 3.11 or 3.12. Found: $pyVersion" -ForegroundColor Yellow
    }
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    $errors += "Node.js is not installed. Please install Node.js 20+ from nodejs.org"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $errors += "Docker is not installed. Please install Docker Desktop"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
}

if ($errors.Count -gt 0) {
    Write-Host "`nMissing prerequisites:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "`nPlease install missing prerequisites and run this script again." -ForegroundColor Yellow
    exit 1
}

# Create .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# Install backend dependencies
Write-Host "`nInstalling backend dependencies..." -ForegroundColor Yellow
Push-Location backend
uv sync --all-extras
Pop-Location

# Install frontend dependencies
Write-Host "`nInstalling frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

# Install pre-commit if available
if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
    Write-Host "`nInstalling pre-commit hooks..." -ForegroundColor Yellow
    pre-commit install
}
else {
    Write-Host "`npre-commit not installed. Install with: pip install pre-commit" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nNext steps:"
Write-Host "  1. Start Docker Desktop"
Write-Host "  2. Run: docker compose up -d"
Write-Host "  3. Open http://localhost:3000 (frontend)"
Write-Host "  4. Open http://localhost:8000/docs (API docs)"
Write-Host ""
