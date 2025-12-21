# 🛡️ Data Deletion Assistant

**Automate your GDPR/CCPA data deletion requests and take back control of your personal information.**

A comprehensive web application that scans your Gmail inbox for data broker communications, generates legally compliant deletion requests, and tracks broker responses—all with an intuitive dashboard and powerful analytics.

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
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
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

### 📧 **Automated Deletion Requests**
- Generate legally compliant GDPR/CCPA deletion request emails
- Pre-filled templates with broker-specific information
- One-click email sending via Gmail API
- Track request status (pending, sent, confirmed, rejected)

- Duplicate-request detection prevents accidental resends and surfaces friendly messaging in the UI

### 📊 **Response Tracking & Analytics**
- Automatic detection of broker responses
- Classify responses: confirmation, rejection, acknowledgment, info request
- Daily automated scans for new responses (Celery Beat scheduling)
- Success rate analytics and broker compliance ranking
- Timeline charts showing request progress over time

- Per-request history timeline (creation, sends, responses, and Gmail rate-limit notices) keeps context in one place

### 📈 **Interactive Dashboard**
- Real-time overview of all deletion activities
- Success rate metrics and confirmation tracking
- Recent broker responses with type badges
- Quick action shortcuts to key features

- Admin-only task queue health widget exposes Celery worker status, queue depth, and refresh controls

### 🎯 **Advanced Analytics**
- Visual charts with recharts library
- Broker compliance ranking (success rate + response time)
- Response type distribution pie charts
- Timeline views (7/30/90 day ranges)
- Average response time tracking

### 👥 **Manual Broker Management**
- Collapsible "Manual Broker Entry" form for quickly adding new brokers (name, domains, privacy email, opt-out URL, category)
- Broker cards highlight whether a deletion request already exists and disable the CTA accordingly
- Inline validation/error handling bubbled up from the backend

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
5. **Response Tracking**: Daily Celery Beat task scans for broker responses
6. **Analytics**: Real-time analytics computed from database

---

## 🎯 Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (recommended)
- **Python 3.11 or 3.12** (not 3.13 - lxml compatibility)
- **Node.js 20+**
- **uv** - Python package manager
- **Google Cloud Project** with Gmail API enabled (for full functionality)

> **Platform-specific instructions**: See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed Windows/Linux/macOS setup guides.

### Quick Start

**Linux/macOS:**
```bash
git clone https://github.com/kirilan/anti-spam.git
cd anti-spam
./scripts/setup.sh   # or: make setup
make dev
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/kirilan/anti-spam.git
cd anti-spam
.\scripts\setup.ps1
docker compose up -d
```

Access the application:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Configuration

#### 1. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create/select a project and enable the **Gmail API**
3. Create OAuth 2.0 credentials (Web application):
   - Redirect URI: `http://localhost:8000/auth/callback`
4. Copy the **Client ID** and **Client Secret**

#### 2. Environment Variables

```bash
cp .env.example .env
```

Required variables in `.env`:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SECRET_KEY=<generate-with-command-below>
ENCRYPTION_KEY=<generate-with-command-below>
```

Generate security keys:

```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Local Development (without Docker)

The backend uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
make install-dev

# Start PostgreSQL and Redis (via Docker or locally)
docker compose up -d db redis

# Run backend
make run-backend

# In another terminal - run Celery worker
make run-worker

# Frontend
cd frontend && npm install && npm run dev
```

### Available Make Commands

```
make help          Show all commands
make dev           Start Docker environment
make test          Run tests
make lint          Run linter
make format        Format code
make migrate       Run database migrations
make logs          View container logs
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
   - **Days back**: How far to scan (default: 90 days)
   - **Max emails**: Maximum emails to process (default: 100)
3. Click **Start Scan**
4. View results in **Email Results** page

### **4. Create Deletion Requests**

1. Navigate to **Deletion Requests** page
2. Click **Create Request**
3. Select a data broker
4. Choose legal framework (GDPR or CCPA)
5. Review the generated email
6. Click **Send Request** to send via Gmail

### **5. Track Responses**

1. Go to **Broker Responses** page
2. Click **Scan for Responses** to manually check for replies
3. View response types:
   - ✅ **Confirmation** - Deletion confirmed
   - ❌ **Rejection** - Request denied
   - ⏳ **Acknowledgment** - Request received, processing
   - ⚠️ **Info Request** - More information needed
   - ❓ **Unknown** - Unable to classify
4. Filter by response type
5. Daily automated scans run at 2 AM UTC

### **6. View Analytics**

1. Navigate to **Analytics** page
2. View success metrics:
   - Total requests and success rate
   - Average response time
   - Timeline charts (requests sent vs confirmations)
   - Broker compliance ranking
   - Response type distribution

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
make test          # Run tests
make test-cov      # With coverage
make lint          # Check code style
make format        # Auto-format code
make typecheck     # Type checking
make check         # Run all checks
```

### Building for Production

```bash
docker compose -f docker-compose.prod.yml up --build
```

---

## 📁 Project Structure

```
anti-spam/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── config.py               # Settings & environment
│   │   ├── database.py             # Database connection
│   │   ├── celery_app.py           # Celery configuration
│   │   ├── logging_config.py       # Structured logging
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic schemas (with validation)
│   │   ├── services/               # Business logic
│   │   ├── api/                    # Route handlers
│   │   ├── tasks/                  # Celery tasks
│   │   ├── templates/              # Email templates (GDPR/CCPA)
│   │   └── utils/
│   ├── tests/                      # pytest tests
│   ├── alembic/                    # Database migrations
│   ├── data/
│   │   └── data_brokers.json       # Known brokers database
│   ├── pyproject.toml              # uv/Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── hooks/                  # Custom hooks
│   │   ├── services/api.ts         # API client
│   │   ├── stores/                 # Zustand stores
│   │   ├── lib/utils.ts            # Utilities
│   │   └── types/                  # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── Makefile                        # Development commands
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔒 Security

### **Data Protection**
- OAuth tokens encrypted at rest using **Fernet** symmetric encryption
- Email content never logged to files
- Secure PostgreSQL connections with SSL support
- Environment variables for sensitive credentials

### **Privacy Compliance**
- All deletion requests follow GDPR Article 17 (Right to Erasure)
- CCPA compliance for California residents
- No third-party data sharing
- User data stored locally in your database

### **Best Practices**
- Use strong, randomly generated `SECRET_KEY` and `ENCRYPTION_KEY`
- Keep `.env` file out of version control (`.gitignore` included)
- Use HTTPS in production (configure Nginx SSL)
- Regularly update dependencies for security patches
- Promote trusted accounts to admin by setting `is_admin = true` in the `users` table (for example via `UPDATE users SET is_admin=true WHERE email='you@example.com';`) and re-authenticating to mint a new JWT

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
- **Bug Reports**: [Open an issue](https://github.com/yourusername/data-deletion-assistant/issues)
- **Feature Requests**: [Start a discussion](https://github.com/yourusername/data-deletion-assistant/discussions)

---

## 📰 Recent Updates

### v1.0.0 - Current Release (December 2024)

**✅ Completed Features**
- ✨ **Response Tracking System** - Automatic broker response detection and classification
- 📊 **Analytics Dashboard** - Success metrics, broker compliance ranking, timeline charts
- 🤖 **Automated Scheduling** - Daily response scans at 2 AM UTC via Celery Beat
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


**Made with ❤️ for privacy advocates everywhere**

*Remember: Your data is yours. Exercise your rights.* 🛡️
## Recent Updates:

- 🔑 **JWT-powered Auth Guard** - Every API now requires bearer tokens minted after Google OAuth, with admin-only scopes
- 🛡️ **Admin Flag Enforcement** - Per-user `is_admin` gate for Celery health, broker sync, and other privileged actions
- 🖊️ **Manual Broker Entry** - UI + API support for adding brokers one at a time with validation
- 📝 **Request Timeline & Rate Limits** - Visual history plus Gmail backoff messaging directly on each request card
- 💻 **Task Queue Monitoring** - Dashboard tile (admin-only) summarizing Celery worker health and queue depth

## 🧞️ Roadmap

### Near-term (next sprint)
- [ ] Ship backend rate limiting & abuse controls on scan/task endpoints
- [ ] Admin management UI (promote/demote users without SQL)
- [ ] Hide admin-only widgets (Celery health, broker sync) for non-admin accounts
- [ ] Broker import/export tooling with CSV/JSON validation
- [ ] Better dashboard error surfaces for expired tokens / 401s

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

**Made with ?? for privacy advocates everywhere**

*Remember: Your data is yours. Exercise your rights.* 📧
