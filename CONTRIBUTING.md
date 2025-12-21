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

### Running the Application

| Command | Description |
|---------|-------------|
| `docker compose up -d` | Start all services |
| `docker compose down` | Stop all services |
| `docker compose logs -f` | View logs |
| `docker compose logs -f backend` | View backend logs |

**Services:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

### Running Tests

```bash
# Windows (PowerShell)
cd backend
uv run pytest
uv run pytest --cov=app --cov-report=term-missing  # with coverage

# Linux/macOS
make test
make test-cov  # with coverage
```

### Code Quality

```bash
# Windows (PowerShell)
cd backend
uv run ruff check app tests        # lint
uv run ruff check --fix app tests  # lint with auto-fix
uv run ruff format app tests       # format
uv run mypy app                    # type check

# Linux/macOS
make lint
make lint-fix
make format
make typecheck
make check  # runs all checks
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

### Database Migrations

```bash
# Windows (PowerShell)
cd backend
uv run alembic upgrade head                    # apply migrations
uv run alembic revision --autogenerate -m "description"  # create new

# Linux/macOS
make migrate
make migrate-new m="description"
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
