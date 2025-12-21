# Demo Recording

This folder contains scripts for recording a demonstration of the quality improvements added to OpenShred.

## Prerequisites

- `asciinema` - Terminal session recorder
- `pv` - Pipe viewer (for typing effect)

```bash
# Ubuntu/Debian
sudo apt install asciinema pv

# macOS
brew install asciinema pv
```

## Recording the Demo

```bash
cd /path/to/anti-spam/demo

# Record the demo
asciinema rec demo.cast -c "./demo-script.sh"

# The recording will be saved to demo.cast
```

## Playback Options

```bash
# Play locally
asciinema play demo.cast

# Play at 2x speed
asciinema play -s 2 demo.cast

# Upload to asciinema.org for sharing
asciinema upload demo.cast
```

## Converting to GIF

For sharing on platforms that don't support asciinema, convert to GIF:

```bash
# Install agg (asciinema gif generator)
cargo install --git https://github.com/asciinema/agg

# Or download binary from:
# https://github.com/asciinema/agg/releases

# Convert to GIF
agg demo.cast demo.gif

# With custom settings
agg --cols 120 --rows 35 --font-size 14 demo.cast demo.gif
```

## What the Demo Shows

1. **Makefile** - Single entry point for all development tasks
2. **uv** - Modern Python package management (10-100x faster than pip)
3. **Pre-commit hooks** - Automated code quality (ruff, ESLint, gitleaks)
4. **pytest** - Comprehensive test suite
5. **GitHub Actions** - CI/CD pipeline
6. **Docker improvements** - Non-root users, multi-stage builds, port config
7. **Documentation** - CONTRIBUTING.md and AGENTS.md

## Customizing

Edit `demo-script.sh` to adjust:
- Typing speed: Change `pv -qL 30` (30 chars/sec)
- Pause duration: Adjust `sleep` values
- Content: Add/remove sections as needed
