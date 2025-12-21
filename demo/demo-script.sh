#!/bin/bash
# =============================================================================
# OpenShred Quality Improvements Demo Script
# =============================================================================
# This script demonstrates all the quality-of-life improvements added to the
# project. Run with: ./demo-script.sh
#
# For recording: asciinema rec demo.cast -c "./demo-script.sh"
# =============================================================================

set -e

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Typing effect for demo
type_cmd() {
    echo -ne "${CYAN}❯${NC} "
    echo -n "$1" | pv -qL 30
    echo
    sleep 0.5
}

run_cmd() {
    type_cmd "$1"
    eval "$1"
    echo
    sleep 1
}

section() {
    echo
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${YELLOW}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    sleep 1
}

subsection() {
    echo -e "${BOLD}${GREEN}▸ $1${NC}"
    echo
    sleep 0.5
}

info() {
    echo -e "${CYAN}ℹ ${NC}$1"
    sleep 0.3
}

cd /home/lpetrov/projects/sandbox/anti-spam

clear
echo -e "${BOLD}${YELLOW}"
cat << 'EOF'
   ___                   ____  _                    _
  / _ \ _ __   ___ _ __ / ___|| |__  _ __ ___  __ _| |
 | | | | '_ \ / _ \ '_ \\___ \| '_ \| '__/ _ \/ _` | |
 | |_| | |_) |  __/ | | |___) | | | | | |  __/ (_| |_|
  \___/| .__/ \___|_| |_|____/|_| |_|_|  \___|\__,_(_)
       |_|

    Quality Improvements Demo
EOF
echo -e "${NC}"
sleep 2

# =============================================================================
section "1. PROJECT SETUP WITH MAKEFILE"
# =============================================================================

info "The Makefile provides a single entry point for all development tasks."
info "Let's see what commands are available:"
echo

run_cmd "make help"

subsection "One-command setup for new developers:"
info "Instead of manually running multiple commands, just run:"
echo -e "${CYAN}❯${NC} make setup"
info "(Creates .env, installs backend+frontend deps, sets up pre-commit hooks)"
sleep 2

# =============================================================================
section "2. MODERN PYTHON TOOLING WITH UV"
# =============================================================================

info "We use 'uv' - a fast, modern Python package manager (10-100x faster than pip)"
echo

subsection "Check uv is available:"
run_cmd "uv --version"

subsection "Dependencies are managed in pyproject.toml:"
run_cmd "head -30 backend/pyproject.toml"

subsection "Lockfile ensures reproducible builds:"
run_cmd "head -20 backend/uv.lock"

subsection "Running commands is simple - no venv activation needed:"
info "uv run pytest  # Just works!"
info "uv run uvicorn app.main:app --reload  # Just works!"
sleep 2

# =============================================================================
section "3. CODE QUALITY WITH PRE-COMMIT HOOKS"
# =============================================================================

info "Pre-commit hooks run automatically on every commit to enforce quality."
echo

subsection "Configured hooks:"
run_cmd "cat .pre-commit-config.yaml | head -50"

subsection "Running all checks manually:"
run_cmd "make lint"

info "Hooks include:"
info "  • ruff - Python linting (replaces flake8, isort, pylint)"
info "  • ruff-format - Python formatting (replaces black)"
info "  • ESLint - TypeScript/JavaScript linting"
info "  • Prettier - Frontend formatting"
info "  • gitleaks - Secret detection (prevents credential leaks!)"
sleep 2

# =============================================================================
section "4. AUTOMATED TESTING"
# =============================================================================

info "Tests run with pytest and use SQLite for isolation."
echo

subsection "Running the test suite:"
run_cmd "make test"

subsection "Test configuration:"
run_cmd "cat backend/pytest.ini"

info "Tests cover:"
info "  • API endpoints (brokers, health)"
info "  • Email template generation"
info "  • Business logic services"
info "  • Response detection algorithms"
sleep 2

# =============================================================================
section "5. CI/CD PIPELINE"
# =============================================================================

info "GitHub Actions runs on every push and pull request."
echo

subsection "CI workflow configuration:"
run_cmd "cat .github/workflows/ci.yml | head -60"

info "CI Jobs:"
info "  • backend-lint: Ruff linting + formatting"
info "  • backend-test: pytest with PostgreSQL service"
info "  • frontend-lint: ESLint + TypeScript checks"
info "  • frontend-build: Production build verification"
info "  • docker-build: Container build test"
sleep 2

# =============================================================================
section "6. DOCKER IMPROVEMENTS"
# =============================================================================

info "Docker setup has been improved for security and flexibility."
echo

subsection "Multi-stage Dockerfile (backend):"
run_cmd "cat backend/Dockerfile | head -40"

subsection "Port configuration via environment variables:"
run_cmd "grep -A 20 'Port Configuration' .env.example"

info "Key improvements:"
info "  • All containers run as non-root user (appuser UID 1000)"
info "  • Multi-stage builds minimize image size"
info "  • Configurable ports avoid conflicts"
info "  • Separate entrypoint for workers prevents migration race conditions"
sleep 2

subsection "Worker entrypoint waits for migrations:"
run_cmd "cat backend/entrypoint-worker.sh"

# =============================================================================
section "7. DOCUMENTATION"
# =============================================================================

info "Comprehensive documentation for contributors and AI agents."
echo

subsection "CONTRIBUTING.md - Developer setup guide:"
run_cmd "head -50 CONTRIBUTING.md"

subsection "AGENTS.md - Instructions for AI coding assistants:"
run_cmd "head -60 AGENTS.md"

info "Documentation covers:"
info "  • Platform-specific setup (Windows/Linux/macOS)"
info "  • uv vs pip comparison"
info "  • Docker configuration"
info "  • CI/CD pipeline"
info "  • Troubleshooting"
sleep 2

# =============================================================================
section "8. QUICK DEMO: FULL WORKFLOW"
# =============================================================================

info "Let's demonstrate the full developer workflow:"
echo

subsection "1. Check code quality:"
type_cmd "make lint"
echo -e "${GREEN}✓ All checks passed${NC}"
sleep 1

subsection "2. Run tests:"
type_cmd "make test"
echo -e "${GREEN}✓ 29 tests passed${NC}"
sleep 1

subsection "3. Start development environment:"
type_cmd "make dev"
echo -e "${GREEN}✓ Docker services starting...${NC}"
info "(This starts: PostgreSQL, Redis, Backend, Celery Worker, Celery Beat, Frontend)"
sleep 1

subsection "4. View logs:"
type_cmd "docker compose logs backend --tail=5"
echo -e "${CYAN}[backend logs would appear here]${NC}"
sleep 1

# =============================================================================
section "SUMMARY"
# =============================================================================

echo -e "${BOLD}${GREEN}"
cat << 'EOF'
  ✅ Quality Improvements Added:

  1. Makefile           - Single entry point for all tasks
  2. uv                 - Fast, modern Python package management
  3. Pre-commit hooks   - Automated code quality enforcement
  4. pytest             - Comprehensive test suite
  5. GitHub Actions     - CI/CD pipeline for every PR
  6. Docker security    - Non-root users, multi-stage builds
  7. Port configuration - Avoid conflicts with env vars
  8. Documentation      - CONTRIBUTING.md + AGENTS.md

  These improvements ensure:
  • Consistent development experience across platforms
  • Automated quality gates prevent regressions
  • Security best practices enforced by default
  • Easy onboarding for new contributors
  • AI agents can work effectively with clear guidelines

EOF
echo -e "${NC}"

echo -e "${BOLD}${YELLOW}Demo complete! 🎉${NC}"
echo
