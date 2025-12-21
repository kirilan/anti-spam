#!/bin/bash
# Bash setup script for Linux/macOS
# Run with: ./scripts/setup.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Data Deletion Assistant...${NC}"

# Check prerequisites
errors=()

if ! command -v python3 &> /dev/null; then
    errors+=("Python is not installed. Please install Python 3.11 or 3.12")
else
    py_version=$(python3 --version 2>&1)
    if [[ ! "$py_version" =~ 3\.(11|12) ]]; then
        echo -e "${YELLOW}Warning: Python version should be 3.11 or 3.12. Found: $py_version${NC}"
    fi
fi

if ! command -v node &> /dev/null; then
    errors+=("Node.js is not installed. Please install Node.js 20+")
fi

if ! command -v docker &> /dev/null; then
    errors+=("Docker is not installed. Please install Docker")
fi

if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

if [ ${#errors[@]} -gt 0 ]; then
    echo -e "\n${RED}Missing prerequisites:${NC}"
    for error in "${errors[@]}"; do
        echo -e "${RED}  - $error${NC}"
    done
    echo -e "\n${YELLOW}Please install missing prerequisites and run this script again.${NC}"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env
fi

# Install backend dependencies
echo -e "\n${YELLOW}Installing backend dependencies...${NC}"
cd backend
uv sync --all-extras
cd ..

# Install frontend dependencies
echo -e "\n${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
npm install
cd ..

# Install pre-commit if available
if command -v pre-commit &> /dev/null; then
    echo -e "\n${YELLOW}Installing pre-commit hooks...${NC}"
    pre-commit install
else
    echo -e "\n${YELLOW}pre-commit not installed. Install with: pip install pre-commit${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Start Docker (if not running)"
echo "  2. Run: make dev  (or: docker compose up -d)"
echo "  3. Open http://localhost:3000 (frontend)"
echo "  4. Open http://localhost:8000/docs (API docs)"
echo ""
