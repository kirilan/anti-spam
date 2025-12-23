# 🛡️ OpenShred

**YOUR OPEN-SOURCE DIGITAL SHREDDER.**
**Automate GDPR/CCPA requests, purge your data from broker databases, and permanently reclaim your inbox.**

A comprehensive web application that scans your Gmail inbox for data broker communications, generates legally compliant deletion requests, and tracks broker responses—all with an intuitive dashboard and powerful analytics.

[Live demo](https://app.dimitroff.work)

![OpenShred demo](https://youtu.be/r8Quc-C7IsY?si=45P1UopaH-G_L43D)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)

---

> [!WARNING]
> **🚧 EARLY DEVELOPMENT VERSION 🚧**
>
> This project is currently in **active development** and should be considered **alpha/beta quality**.
>
> **Known Limitations:**
> - ⚠️ Not production-ready - use at your own risk
> - 🐛 May contain bugs and incomplete features
> - 🔄 APIs and database schema may change without notice
> - 📝 Documentation may be incomplete or outdated
> - 🔒 Security features are still being hardened
>
> **Recommended Usage:**
> - ✅ Development and testing environments only
> - ✅ Personal experimentation and learning
> - ✅ Contributing to development
> - ❌ Not recommended for production use with real personal data
>
> **Contributions welcome!** Help us make this production-ready. See [Contributing](#-contributing) section below.

---

## 📋 Table of Contents

- [Features](#-features)
- [Hourly Response Scan Workflow](#-hourly-response-scan-workflow)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Configuration](#configuration)
- [Usage](#-usage)
- [Development](#-development)
- [Project Structure](#-project-structure)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)
- [Recent Updates](#-recent-updates)
- [Roadmap](#-roadmap)

---

## ✨ Features

### 🔍 **Intelligent Email Scanning**
- Scans Gmail inbox for communications from 15+ known data brokers
- Keyword-based email classification with confidence scoring
- Domain matching against known broker databases
- Customizable scan depth (days back, max emails)
- Scan history log with pagination and totals
- Email results live inside the Scan Emails page with broker-only toggle and pagination

### 📧 **Automated Deletion Requests**
- Generate legally compliant GDPR/CCPA deletion request emails
- Pre-filled templates with broker-specific information
- One-click email sending via Gmail API
- Track request status (pending, sent, confirmed, rejected)

- Duplicate-request detection prevents accidental resends and surfaces friendly messaging in the UI

### 📊 **Response Tracking & Analytics**
- Automatic detection of broker responses
- Classify responses: confirmation, rejection, acknowledgment, info request
- Scheduled scans for new responses via Celery Beat (hourly during active development, configurable)
- Success rate analytics and broker compliance ranking
- Timeline charts showing request progress over time

- Per-request history timeline (creation, sends, responses, and Gmail rate-limit notices) keeps context in one place
- Unified Deletion Requests view with inline responses, match method, and manual reclassification

### 📈 **Interactive Dashboard**
- Real-time overview of all deletion activities
- Success rate metrics and confirmation tracking
- Recent broker responses with type badges
- Quick action shortcuts to key features

- Task queue health widget exposes Celery worker status, queue depth, and refresh controls for admin users

### 🤖 **AI Assist (Per-User)**
- Each user configures their own Gemini API key + model selection in Settings
- API keys encrypted at rest using Fernet encryption - completely isolated per user
- AI Assist reclassifies all responses on a thread when invoked
- Structured JSON output shown in-app and logged in the activity feed
- Status updates only when model output is valid JSON with confidence ≥ 0.75
- Zero cross-user access - your API key is used only for your requests

### 🎯 **Advanced Analytics**
- Visual charts with recharts library
- Broker compliance ranking (success rate + response time)
- Response type distribution pie charts
- Timeline views (7/30/90 day ranges)
- Average response time tracking

### 👥 **Broker Management**
- All users can sync brokers from the built-in directory
- Collapsible "Manual Broker Entry" form for quickly adding new brokers (name, domains, privacy email, opt-out URL, category)
- Broker cards highlight whether a deletion request already exists and disable the CTA accordingly
- Inline validation/error handling bubbled up from the backend
- Community-driven broker database available to all users

---

## ⏱️ Hourly Response Scan Workflow

During active development, the response scan runs hourly via Celery Beat. This job rechecks Gmail for broker replies and updates request statuses.

1. Celery Beat triggers `scan_all_users_for_responses` at the top of each hour (UTC).
2. The task finds users with sent deletion requests and enqueues `scan_for_responses_task` per user.
3. Each per-user task builds a Gmail query from broker domains and the oldest sent request date (or 7-day fallback).
4. Gmail API searches the inbox and fetches up to 50 full messages matching that query.
5. Existing responses are reclassified; new responses are created if the Gmail message ID is new.
6. Responses are matched to deletion requests and can update status on high confidence (or thread match).
7. Results are committed and logged as `response_scanned` with JSON details and `source="automated"`.
8. The Scan History panel shows these runs alongside manual mailbox scans.

To switch back to daily scheduling, adjust the Beat schedule in `backend/app/celery_app.py`.

---

## 🚀 Tech Stack

### **Backend**
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for PostgreSQL
- **Celery** - Distributed task queue for background jobs
- **Celery Beat** - Periodic task scheduling
- **Google Gmail API** - OAuth2 authentication and email access
- **Pydantic** - Data validation and settings management
- **Cryptography** - Fernet encryption for OAuth tokens

### **Frontend**
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **TanStack Query** (React Query) - Data fetching and caching
- **Zustand** - Lightweight state management
- **React Router** - Client-side routing
- **shadcn/ui** - Accessible component library
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Charting library for analytics

### **Infrastructure**
- **PostgreSQL 15** - Relational database
- **Redis 7** - Cache and message broker
- **Docker & Docker Compose** - Containerization
- **Nginx** - Frontend web server
- **Caddy** - Reverse proxy + automated TLS for production

---

## 🏗️ Architecture

```
┌─────────────────┐
│   React SPA     │  ← User Interface (TypeScript + Tailwind)
│  (Port 3000)    │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI        │  ← Backend API + Gmail OAuth
│  (Port 8000)    │
└────────┬────────┘
         │
    ┌────┴─────┬──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌───────┐ ┌─────────┐
│Postgres│ │ Redis │ │  Gmail  │
│   DB   │ │ Queue │ │   API   │
└────────┘ └───┬───┘ └─────────┘
               │
        ┌──────┴───────┐
        │              │
        ▼              ▼
   ┌────────┐    ┌──────────┐
   │ Celery │    │  Celery  │
   │ Worker │    │   Beat   │
   └────────┘    └──────────┘
```

### **Data Flow**

1. **Authentication**: User authorizes Gmail access via OAuth2
2. **Scanning**: Celery worker scans inbox for broker emails
3. **Request Creation**: User creates deletion requests from dashboard
4. **Email Sending**: Automated emails sent via Gmail API
5. **Response Tracking**: Scheduled Celery Beat task scans for broker responses
6. **Analytics**: Real-time analytics computed from database

---

## 🎯 Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (recommended)
- **Python 3.11 or 3.12** (not 3.13 - lxml compatibility)
- **Node.js 20+**
- **uv** - Python package manager (recommended for local development)
- **Google Cloud Project** with Gmail API enabled (for full functionality)

For Docker-only usage, you can skip Python, Node.js, and uv; they are only required for local development.

> **Platform-specific instructions**: See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed Windows/Linux/macOS setup guides.

### Quick Start

**Linux/macOS:**
```bash
git clone https://github.com/kirilan/OpenShred.git
cd OpenShred
./scripts/setup.sh   # or: make setup
make dev
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/kirilan/OpenShred.git
cd OpenShred
.\scripts\setup.ps1
docker compose up -d
```

Access the application:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Configuration

#### 1. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to **APIs & Services > Library**
   - Search for **Gmail API** and click **Enable**
4. Create OAuth 2.0 Credentials:
   - Go to **APIs & Services > Credentials**
   - Click **Create Credentials > OAuth client ID**
   - Application type: **Web application**
   - Name: `OpenShred`
   - **Authorized redirect URIs**:
     - `http://localhost:8000/auth/callback`
     - `http://localhost:3000/oauth-callback`
   - Click **Create** and copy the **Client ID** and **Client Secret**

#### 2. Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Database (Docker default)
DATABASE_URL=postgresql://postgres:postgres@db:5432/antispam

# Redis (Docker default)
REDIS_URL=redis://redis:6379/0

# Security Keys (generate these!)
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Environment & URLs
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
VITE_API_URL=http://localhost:8000

# Reverse proxy (only needed when ENVIRONMENT=production)
APP_HOSTNAME=app.example.com
API_HOSTNAME=api.example.com
CADDY_ACME_EMAIL=admin@example.com
```

**Generate Security Keys:**

```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### 3. Start the Application

```bash
make dev  # or: docker compose up --build
```

This will start:
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`
- **FastAPI backend** on port `8000`
- **Celery worker** for background tasks
- **Celery beat** for scheduled tasks
- **React frontend** on port `3000`

#### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 🌐 Production via Caddy Reverse Proxy (Recommended)

When you are ready to expose the app publicly, the preferred method is to use the built-in Caddy profile from `docker-compose.yml`:

1. Set `ENVIRONMENT=production`, update `FRONTEND_URL` to `https://<your app hostname>`, and set `VITE_API_URL` to `https://<your API hostname>` inside `.env`.
2. Provide `APP_HOSTNAME`, `API_HOSTNAME`, and `CADDY_ACME_EMAIL` so the proxy knows which domains to serve and which email to use for ACME.
3. Create DNS `A`/`AAAA` records for both hostnames pointing to the server that will run Docker.
4. Build the production images and start the stack with the proxy enabled:
   ```bash
   docker compose --profile production up -d --build
   ```
5. Caddy (configured via `Caddyfile`) will terminate TLS on ports `80/443`, obtain certificates automatically, and forward traffic to the internal `frontend` and `backend` services while the FastAPI app locks CORS down to `FRONTEND_URL`.

If you already run your own reverse proxy and TLS termination, you can use `docker-compose.prod.yml` instead and expose only the frontend service (no Caddy).

### Local Development (without Docker)

You can use either **uv** (recommended) or **pip** for backend development.

#### Using uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install dependencies
make install-dev

# Start PostgreSQL and Redis
docker compose up -d db redis

# Run backend (uv handles venv automatically)
make run-backend      # or: cd backend && uv run uvicorn app.main:app --reload

# Run tests
make test             # or: cd backend && uv run pytest
```

#### Using pip (Alternative)

```bash
# Create and activate virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate     # Linux/macOS
# .venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements-dev.txt

# Run backend (venv must be activated)
uvicorn app.main:app --reload

# Run tests
pytest
```

> **Detailed guide**: See [CONTRIBUTING.md](CONTRIBUTING.md) for the full backend development workflow, including dependency management and the comparison between uv and pip.

### Available Make Commands

```
make help              Show all commands
make dev               Start Docker environment
make test              Run tests
make test-all          Run backend + frontend tests
make lint              Run linters via pre-commit
make check             Run lint + test
make sync-requirements Regenerate requirements.txt from pyproject.toml
```

---

## 📖 Usage

### **1. Login & Authenticate**

1. Navigate to http://localhost:3000
2. Click **Login with Gmail**
3. Authorize the application to access your Gmail account
4. You'll be redirected to the dashboard

### **2. Load Data Brokers**

1. Navigate to **Data Brokers** page
2. Click **Sync Brokers** to load 15+ known data brokers
3. View broker information (name, website, privacy email, domains)

### **3. Scan Your Inbox**

1. Go to **Scan Emails** page
2. Configure scan parameters:
   - **Days back**: How far to scan (default: 1 day)
   - **Max emails**: Maximum emails to process (default: 100)
3. Click **Start Scan**
4. Review scan history and results in the same Scan Emails screen (broker-only by default)

### **4. Create Deletion Requests**

1. Navigate to **Deletion Requests** page
2. Click **Create Request**
3. Select a data broker
4. Choose legal framework (GDPR or CCPA)
5. Review the generated email
6. Click **Send Request** to send via Gmail

### **5. Track Responses**

1. Go to **Deletion Requests** page
2. Click **Scan for Responses** to manually check for replies
3. Review responses inline with each request and the match reason
4. Use manual reclassification or AI Assist as needed
5. View response types:
   - ✅ **Confirmation** - Deletion confirmed
   - ❌ **Rejection** - Request denied
   - ⏳ **Acknowledgment** - Request received, processing
   - ⚠️ **Info Request** - More information needed
   - ❓ **Unknown** - Unable to classify
6. Filter by response type
7. Scheduled response scans run hourly during development (configurable in Celery Beat)

### **6. Configure AI Assist (Optional)**

1. Navigate to **Settings** page
2. Enter your Google Gemini API key
3. Select your preferred model (e.g., gemini-1.5-flash, gemini-1.5-pro)
4. Your API key is encrypted and stored securely - only you can use it
5. Use AI Assist on the Deletion Requests page to reclassify responses

### **7. View Analytics**

1. Navigate to **Analytics** page
2. View success metrics:
   - Total requests and success rate
   - Average response time
   - Timeline charts (requests sent vs confirmations)
   - Broker compliance ranking
   - Response type distribution
3. Admin users can view task queue health on the Dashboard (worker status, active tasks, queue depth)

---

## 🛠️ Development

### Backend (uv)

The backend uses [uv](https://docs.astral.sh/uv/) for fast, reliable dependency management.

```bash
# Install dependencies
make install-dev

# Run locally (requires PostgreSQL + Redis)
make run-backend    # API server
make run-worker     # Celery worker
make run-beat       # Celery beat scheduler
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at http://localhost:5173

### Database Migrations

```bash
# Run migrations
make migrate

# Create new migration
make migrate-new m="Add new table"

# View migration history
make migrate-history
```

### Testing & Code Quality

```bash
make test              # Run backend tests
make test-cov          # Backend tests with coverage
make test-frontend     # Run frontend tests
make test-all          # Run all tests
make lint              # Check code style
make format            # Auto-format code
make check             # Run all checks (lint + tests)
```

### Docker Configuration

The project uses multi-stage Docker builds with security-focused defaults:

| File / Profile | Purpose | Target |
|------|---------|--------|
| `docker-compose.yml` | Local development | `development` stage |
| `docker-compose.yml` (profile: `production`) | Production with Caddy reverse proxy (recommended) | `production` stage |
| `docker-compose.prod.yml` | Production with external reverse proxy | `production` stage |

**Security Features:**
- All containers run as non-root user (`appuser` UID 1000)
- Multi-stage builds minimize image size
- Production images contain no build tools

**Port Configuration** (via `.env`):
```env
POSTGRES_PORT=5432    # PostgreSQL
REDIS_PORT=6379       # Redis
BACKEND_PORT=8000     # FastAPI backend
FRONTEND_PORT=3000    # Frontend (dev) / 80 (prod)
```

**Building for Production (Caddy profile):**
```bash
docker compose --profile production up -d --build
```

**Building for Production (external reverse proxy):**
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### CI/CD Pipeline

GitHub Actions runs automatically on every push and pull request:

| Job | Description |
|-----|-------------|
| `backend-lint` | Ruff linting + formatting check |
| `backend-test` | pytest with PostgreSQL service |
| `frontend-lint` | ESLint + TypeScript check |
| `frontend-test` | Vitest with coverage |
| `frontend-build` | Production build test |
| `docker-build` | Docker image build test |

Pre-commit hooks enforce code quality locally before commits.

---

## 📁 Project Structure

```
OpenShred/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Settings & environment config
│   │   ├── database.py             # Database connection
│   │   ├── celery_app.py           # Celery configuration
│   │   ├── logging_config.py       # Structured logging
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── data_broker.py
│   │   │   ├── email_scan.py
│   │   │   ├── deletion_request.py
│   │   │   └── broker_response.py
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/               # Business logic layer
│   │   │   ├── gmail_service.py          # Gmail API wrapper
│   │   │   ├── email_scanner.py          # Inbox scanning
│   │   │   ├── broker_detector.py        # Email classification
│   │   │   ├── broker_service.py         # Broker CRUD
│   │   │   ├── deletion_request_service.py
│   │   │   ├── response_detector.py      # Response type detection
│   │   │   ├── response_matcher.py       # Match responses to requests
│   │   │   └── analytics_service.py      # Analytics calculations
│   │   ├── tasks/                  # Celery tasks
│   │   │   └── email_tasks.py
│   │   ├── api/                    # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── brokers.py
│   │   │   ├── emails.py
│   │   │   ├── requests.py
│   │   │   ├── responses.py
│   │   │   └── analytics.py
│   │   ├── templates/              # Email templates (GDPR/CCPA)
│   │   └── utils/
│   │       └── email_templates.py  # GDPR/CCPA email templates
│   ├── tests/                      # pytest tests
│   ├── alembic/                    # Database migrations
│   ├── data/
│   │   └── data_brokers.json       # Known data broker database
│   ├── pyproject.toml              # uv/Python dependencies
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/               # Authentication components
│   │   │   ├── dashboard/          # Main dashboard
│   │   │   ├── emails/             # Email scanner & list
│   │   │   ├── brokers/            # Broker management
│   │   │   ├── requests/           # Deletion requests
│   │   │   ├── responses/          # Response tracking
│   │   │   ├── analytics/          # Analytics dashboard
│   │   │   ├── layout/             # Navigation & layout
│   │   │   └── ui/                 # shadcn/ui components
│   │   ├── hooks/                  # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useEmails.ts
│   │   │   ├── useBrokers.ts
│   │   │   ├── useRequests.ts
│   │   │   ├── useResponses.ts
│   │   │   └── useAnalytics.ts
│   │   ├── services/
│   │   │   └── api.ts              # Axios API client
│   │   ├── stores/
│   │   │   └── authStore.ts        # Zustand auth store
│   │   ├── test/                   # Test utilities and mocks
│   │   ├── types/                  # TypeScript type definitions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
├── Makefile                        # Development commands
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── CONTRIBUTING.md                 # Contributor guide
├── LICENSE
└── README.md
```

---

## 🔒 Security

### **Data Protection**
- **OAuth tokens** encrypted at rest using **Fernet** symmetric encryption
- **Gemini API keys** encrypted at rest per user - zero cross-user access
- **JWT authentication** on all API endpoints - user data completely isolated
- Email content never logged to files
- Secure PostgreSQL connections with SSL support
- Environment variables for sensitive credentials

### **Privacy Compliance**
- All deletion requests follow GDPR Article 17 (Right to Erasure)
- CCPA compliance for California residents
- No third-party data sharing
- User data stored locally in your database
- AI features use per-user API keys with encrypted storage

### **Best Practices**
- Use strong, randomly generated `SECRET_KEY` and `ENCRYPTION_KEY`
- Keep `.env` file out of version control (`.gitignore` included)
- Use HTTPS in production (configure Nginx SSL or use Caddy)
- Regularly update dependencies for security patches
- Most features are available to all users; admin access is required for task queue health and admin endpoints

---

## 🤝 Contributing

Contributions are welcome! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed setup instructions for Windows, Linux, and macOS.

### Quick Steps:
1. **Fork the repository**
2. **Set up your environment**: `./scripts/setup.sh` (Linux/macOS) or `.\scripts\setup.ps1` (Windows)
3. **Create a feature branch**: `git checkout -b feature/amazing-feature`
4. **Make your changes** (pre-commit hooks run automatically)
5. **Push and open a Pull Request**

### **Areas for Contribution**
- Add more data brokers to `backend/data/data_brokers.json`
- Improve response detection algorithms
- Add internationalization (i18n)
- Create mobile-responsive designs
- Write comprehensive tests
- Improve documentation

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### What This Means:
✅ Commercial use
✅ Modification
✅ Distribution
✅ Private use
❌ Liability
❌ Warranty

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- Icons from [Lucide](https://lucide.dev/)
- Charts by [Recharts](https://recharts.org/)
- Inspired by the need for privacy rights enforcement

---

## 📞 Support

If you encounter issues:

- **Google OAuth Setup**: See [Google Cloud Documentation](https://cloud.google.com/docs/authentication)
- **API Usage**: Check the interactive docs at http://localhost:8000/docs
- **Bug Reports**: [Open an issue](https://github.com/kirilan/OpenShred/issues)
- **Feature Requests**: [Start a discussion](https://github.com/kirilan/OpenShred/discussions)

---

## 📰 Recent Updates

### v1.2.x - Democratization Release (December 2025)

**Feature Democratization**
- 🎉 **All features now available to all authenticated users** - removed admin role requirements
- All users can create/sync data brokers and access analytics; admin users can view task queue health
- Gemini API keys encrypted at rest per user with complete isolation
- AI Assist fully per-user - your API key only classifies your responses
- Updated test suite to reflect democratized feature access

**Security Enhancements**
- Gemini API key encryption using Fernet - stored securely per user
- JWT authentication on all endpoints with complete user data isolation
- Zero cross-user access to API keys or data
- Database migration system using Alembic for schema changes

**Infrastructure Improvements**
- Fixed Nginx proxy configuration for all API endpoints
- Removed unnecessary userId query parameters (backend uses JWT auth)
- Python version constraint (3.11-3.12) to avoid build issues
- All CI/CD checks passing (29/29 backend tests, full frontend test suite)

### v1.1.x - AI Assist & Analytics (December 2025)

**Highlights**
- AI Assist with per-user Gemini API key + model selection, structured JSON output dialog, and activity logging
- Deletion Requests view now includes broker responses, match method, manual reclassification, and AI assist entry point
- Scan Emails refresh: defaults (1 day/100 emails), paginated results + scan history with totals, broker-only toggle
- Scan history includes manual and automated response scans
- Settings page centralizes theme toggle and AI configuration

**Authentication & Security**
- JWT auth guard on every API request
- Manual broker entry UI with backend validation
- Request timeline entries include Gmail rate-limit messaging
- Admin-only task queue health widget for worker status and queue depth

**Developer Experience**
- Frontend test suite with Vitest + React Testing Library + MSW
- CI/CD pipeline with GitHub Actions (lint, test, build, docker)
- Makefile with common development commands
- uv for fast Python dependency management
- Pre-commit hooks for code quality

### v1.0.0 - Initial Release (December 2024)

**✅ Completed Features**
- ✨ **Response Tracking System** - Automatic broker response detection and classification
- 📊 **Analytics Dashboard** - Success metrics, broker compliance ranking, timeline charts
- 🤖 **Automated Scheduling** - Scheduled response scans via Celery Beat (hourly in dev; configurable)
- 📧 **Automated Email Sending** - One-click deletion request sending via Gmail API
- 🎨 **Enhanced Dashboard** - Success rate metrics, recent responses, quick actions
- 📈 **Interactive Charts** - Timeline visualizations with recharts library
- 🔍 **Response Classification** - 5 response types with confidence scoring
- 🔗 **Response Matching** - Automatic linking of broker replies to deletion requests
- ⚡ **Background Processing** - Celery workers for async email operations
- 🎯 **Auto-status Updates** - Requests automatically marked as confirmed/rejected

**🏗️ Core Infrastructure**
- Full React SPA with TypeScript
- FastAPI backend with PostgreSQL
- Celery + Redis for task queue
- Docker Compose deployment
- OAuth2 Gmail integration
- End-to-end encrypted token storage

---

## 🧞️ Roadmap

### Near-term (next sprint)
- [x] ~~Democratize all features - remove admin requirements~~ ✅ Completed in v1.2.x
- [x] ~~Per-user AI Assist with encrypted API keys~~ ✅ Completed in v1.2.x
- [ ] Ship backend rate limiting & abuse controls on scan/task endpoints
- [ ] Broker import/export tooling with CSV/JSON validation
- [ ] Better dashboard error surfaces for expired tokens / 401s
- [ ] User profile page with API key management and usage stats

### Mid-term (v1.5)
- [ ] Customizable email templates plus identity/attachment support
- [ ] Manual response overrides and request notes
- [ ] Dark mode plus advanced filtering/search across tables
- [ ] Export deletion history & analytics (CSV/PDF)
- [ ] Automated follow-up reminders with Slack/email notifications

### Long-term (v2.0 vision)
- [ ] Additional email providers (Outlook, Proton, Yahoo)
- [ ] Mobile/desktop companions & browser extension
- [ ] Multi-user workspaces with role-based access control
- [ ] ML-assisted broker detection and response parsing
- [ ] Community-driven broker database & public compliance leaderboard

---

Made with care for privacy advocates everywhere.

Remember: Your data is yours. Exercise your rights. 🛡️
