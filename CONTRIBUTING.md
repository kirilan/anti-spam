# Contributing Guide

## Prerequisites

- **Python 3.11 or 3.12** (not 3.13 - lxml compatibility issue)
- **Node.js 20+**
- **Docker & Docker Compose**
- **uv** (Python package manager)
- **Git**

## Platform-Specific Setup

### Windows

1. **Install Python 3.11/3.12**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Install Node.js 20+**
   - Download from [nodejs.org](https://nodejs.org/)

3. **Install Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
   - Enable WSL2 backend for better performance

4. **Install uv**
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

5. **Install pre-commit**
   ```powershell
   pip install pre-commit
   ```

6. **Clone and setup**
   ```powershell
   git clone <repository-url>
   cd anti-spam

   # Create .env from example
   copy .env.example .env

   # Install backend dependencies
   cd backend
   uv sync --all-extras
   cd ..

   # Install frontend dependencies
   cd frontend
   npm install
   cd ..

   # Install pre-commit hooks
   pre-commit install
   ```

7. **Start development environment**
   ```powershell
   docker compose up -d
   ```

### Linux / macOS

1. **Install Python 3.11/3.12**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install python3.11 python3.11-venv

   # macOS (with Homebrew)
   brew install python@3.11
   ```

2. **Install Node.js 20+**
   ```bash
   # Using nvm (recommended)
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   nvm install 20
   nvm use 20

   # Or using package manager
   # Ubuntu/Debian
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt install -y nodejs
   ```

3. **Install Docker**
   ```bash
   # Ubuntu/Debian
   sudo apt install docker.io docker-compose-v2
   sudo usermod -aG docker $USER
   # Log out and back in for group changes

   # macOS
   brew install --cask docker
   ```

4. **Install uv**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

5. **Install pre-commit**
   ```bash
   pip install pre-commit
   # or
   pipx install pre-commit
   ```

6. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd anti-spam

   # One-command setup
   make setup

   # Or manually:
   cp .env.example .env
   cd backend && uv sync --all-extras && cd ..
   cd frontend && npm install && cd ..
   pre-commit install
   ```

7. **Start development environment**
   ```bash
   make dev
   # or
   docker compose up -d
   ```

## Development Workflow

### Running the Application (Docker)

| Command | Description |
|---------|-------------|
| `make dev` | Start all services |
| `docker compose down` | Stop all services |
| `docker compose logs -f` | View logs |
| `docker compose logs -f backend` | View backend logs |

**Services:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## Backend Development

You can choose between **uv** (recommended) or **pip** for Python package management.

### Option 1: uv (Recommended)

`uv` is a fast, modern Python package manager that handles virtual environments automatically.

```bash
# Initial setup
make setup                    # Creates .env, installs deps, sets up pre-commit

# Daily development
cd backend
uv run pytest                 # Run tests
uv run uvicorn app.main:app --reload  # Start dev server
uv run alembic upgrade head   # Run migrations

# Or use Makefile shortcuts from project root
make test                     # Run tests
make run-backend              # Start backend
make migrate                  # Run migrations

# Adding dependencies
cd backend
uv add package-name           # Add to pyproject.toml and install
uv add --dev package-name     # Add dev dependency
make sync-requirements        # Regenerate requirements.txt for pip users
```

**Key point**: `uv run` automatically uses the virtual environment in `backend/.venv` - no need to activate it manually.

### Option 2: pip (Traditional)

For users who prefer standard pip or can't install uv.

```bash
# Initial setup
cd backend
python -m venv .venv
source .venv/bin/activate     # Linux/macOS
# .venv\Scripts\activate      # Windows

pip install -r requirements-dev.txt

# Daily development (with venv activated)
pytest                        # Run tests
uvicorn app.main:app --reload # Start dev server
alembic upgrade head          # Run migrations

# Or use Makefile (after activating venv)
make install-pip-dev          # Install deps via pip

# Adding dependencies
# 1. Edit pyproject.toml manually
# 2. Run: make sync-requirements
# 3. Run: pip install -r requirements-dev.txt
```

**Key point**: You must activate the virtual environment before running commands.

### Comparison

| Aspect | uv | pip |
|--------|-----|-----|
| Speed | ~10-100x faster | Standard |
| Venv management | Automatic | Manual activation |
| Lockfile | `uv.lock` (reproducible) | None by default |
| Adding deps | `uv add pkg` | Edit pyproject.toml + sync |
| Running commands | `uv run cmd` | Activate venv first |

### Dependency Management

**Source of truth**: `backend/pyproject.toml`

The requirements files are auto-generated for pip compatibility:
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Production + dev dependencies

When you modify dependencies:
1. Edit `pyproject.toml` (or use `uv add`)
2. Run `make sync-requirements` to update requirements files
3. Commit all three files

---

### Code Quality

```bash
# Run all linters via pre-commit
make lint

# Format code
make format

# Run all checks (lint + test)
make check
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

### Database Migrations

```bash
# Apply migrations
make migrate

# Create new migration
make migrate-new m="description"

# View migration history
cd backend && uv run alembic history
```

## Project Structure

```
anti-spam/
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   │   ├── api/      # Route handlers
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── tasks/    # Celery tasks
│   ├── tests/        # pytest tests
│   └── migrations/   # Database migrations
├── frontend/          # React frontend
│   └── src/
│       ├── components/
│       ├── hooks/
│       ├── services/
│       └── stores/
├── .github/workflows/ # CI/CD pipelines
└── docker-compose.yml
```

## Docker Configuration

### Development vs Production

The project uses multi-stage Docker builds with separate configurations:

| File | Purpose | Target |
|------|---------|--------|
| `docker-compose.yml` | Local development | `development` stage |
| `docker-compose.prod.yml` | Production deployment | `production` stage |

### Security: Non-Root Containers

All containers run as non-root users for security:

- **Backend/Workers**: Run as `appuser` (UID 1000)
- **Frontend (nginx)**: Run as `appuser` (UID 1000)
- **Development**: Uses host UID/GID for volume mount compatibility

### Port Configuration

Default ports can conflict with other services. Configure via `.env`:

```env
POSTGRES_PORT=5432    # PostgreSQL
REDIS_PORT=6379       # Redis
BACKEND_PORT=8000     # FastAPI backend
FRONTEND_PORT=3000    # Frontend (nginx)
```

### Useful Docker Commands

```bash
# View running containers
docker compose ps

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f backend

# Rebuild images after Dockerfile changes
docker compose build

# Full reset (removes data volumes)
docker compose down -v && docker compose up -d

# Run command in container
docker compose exec backend alembic upgrade head

# Run one-off container (for migrations)
docker compose run --rm --no-deps --entrypoint "" backend alembic revision --autogenerate -m "description"
```

---

## CI/CD Pipeline

GitHub Actions runs on every push and pull request:

| Job | Description |
|-----|-------------|
| `backend-lint` | Ruff linting + formatting check |
| `backend-test` | pytest with coverage |
| `frontend-lint` | ESLint + TypeScript check |
| `frontend-build` | Production build test |
| `docker-build` | Docker image build test |

### Running CI Checks Locally

```bash
# Run all pre-commit hooks (same as CI lint)
make lint

# Run backend tests
make test

# Run frontend checks
cd frontend && npm run lint && npm run typecheck && npm run build
```

---

## Troubleshooting

### Windows: Docker not starting
- Ensure WSL2 is installed and enabled
- Run Docker Desktop as Administrator

### Windows: Permission denied errors
- Run PowerShell as Administrator
- Or use Git Bash instead of PowerShell

### Python 3.13 errors
- This project requires Python 3.11 or 3.12 due to lxml compatibility
- Check version: `python --version`

### Pre-commit hook failures
- Run `pre-commit run --all-files` to see detailed errors
- Fix issues and commit again

### Database connection issues
- Ensure Docker containers are running: `docker compose ps`
- Check logs: `docker compose logs db`
- Reset database: `docker compose down -v && docker compose up -d`

### Port conflicts
- Check which ports are in use: `ss -tuln | grep -E ':(5432|6379|8000|3000)'`
- Configure alternative ports in `.env` file

### File permission issues with Docker volumes
- Development containers use `user: "${UID:-1000}:${GID:-1000}"` to match host user
- If files are owned by root, you may need to fix ownership manually
