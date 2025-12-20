# 🛡️ Data Deletion Assistant

**Automate your GDPR/CCPA data deletion requests and take back control of your personal information.**

A comprehensive web application that scans your Gmail inbox for data broker communications, generates legally compliant deletion requests, and tracks broker responses—all with an intuitive dashboard and powerful analytics.

<video src="https://raw.githubusercontent.com/kirilan/anti-spam/kirilan-asset/anti-spam.mp4" controls playsinline muted></video>

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

- Admin-only task queue health widget exposes Celery worker status, queue depth, and refresh controls

### 🤖 **AI Assist**
- Per-user Gemini API key + model selection in Settings
- AI Assist reclassifies all responses on a thread when invoked
- Structured JSON output shown in-app and logged in the activity feed
- Status updates only when model output is valid JSON with confidence ≥ 0.75

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
  - OR **Python 3.11+**, **Node.js 20+**, **PostgreSQL 15**, **Redis 7**
- **Google Cloud Project** with Gmail API enabled
- **Gmail Account** for testing

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/kirilan/anti-spam.git
cd anti-spam
```

#### 2. Set Up Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to **APIs & Services > Library**
   - Search for **Gmail API** and click **Enable**
4. Create OAuth 2.0 Credentials:
   - Go to **APIs & Services > Credentials**
   - Click **Create Credentials > OAuth client ID**
   - Application type: **Web application**
   - Name: `Data Deletion Assistant`
   - **Authorized redirect URIs**:
     - `http://localhost:8000/auth/callback`
     - `http://localhost:3000/oauth-callback`
   - Click **Create** and copy the **Client ID** and **Client Secret**

#### 3. Configure Environment Variables

Create a `.env` file in the project root:

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

#### 4. Start the Application

```bash
docker-compose up --build
```

This will start:
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`
- **FastAPI backend** on port `8000`
- **Celery worker** for background tasks
- **Celery beat** for scheduled tasks
- **React frontend** on port `3000`

#### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 🌐 Production via Caddy Reverse Proxy

When you are ready to expose the app publicly:

1. Set `ENVIRONMENT=production`, update `FRONTEND_URL` to `https://<your app hostname>`, and set `VITE_API_URL` to `https://<your API hostname>` inside `.env`.
2. Provide `APP_HOSTNAME`, `API_HOSTNAME`, and `CADDY_ACME_EMAIL` so the proxy knows which domains to serve and which email to use for ACME.
3. Create DNS `A`/`AAAA` records for both hostnames pointing to the server that will run Docker.
4. Build the production images and start the stack with the proxy enabled:
   ```bash
   docker compose --profile production up -d --build
   ```
5. Caddy (configured via `Caddyfile`) will terminate TLS on ports `80/443`, obtain certificates automatically, and forward traffic to the internal `frontend` and `backend` services while the FastAPI app locks CORS down to `FRONTEND_URL`.

Switching `ENVIRONMENT` back to `development` lets you continue running entirely on `localhost` without the reverse proxy.

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

### **Run Without Docker**

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Start Celery worker:
```bash
celery -A app.celery_app worker --loglevel=info
```

Start Celery beat:
```bash
celery -A app.celery_app beat --loglevel=info
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

### **Database Migrations**

Currently using `init_db()` which creates tables on startup. For production, use Alembic:

```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### **Running Tests**

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### **Building for Production**

```bash
docker-compose -f docker-compose.prod.yml up --build
```

---

## 📁 Project Structure

```
data-deletion-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Settings & environment config
│   │   ├── database.py             # Database connection
│   │   ├── celery_app.py           # Celery configuration
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
│   │   └── utils/
│   │       └── email_templates.py  # GDPR/CCPA email templates
│   ├── data/
│   │   └── data_brokers.json       # Known data broker database
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
│   │   ├── types/                  # TypeScript type definitions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── LICENSE
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

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

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

### v1.1.x - Current Development (December 2025)

**Highlights**
- AI Assist with per-user Gemini API key + model selection, structured JSON output dialog, and activity logging
- Deletion Requests view now includes broker responses, match method, manual reclassification, and AI assist entry point
- Scan Emails refresh: defaults (1 day/100 emails), paginated results + scan history with totals, broker-only toggle
- Scan history includes manual and automated response scans
- Settings page centralizes theme toggle and AI configuration

**Security & Admin**
- JWT auth guard on every API request with admin-only scopes
- Per-user `is_admin` gate for privileged actions (Celery health, broker sync, etc.)
- Manual broker entry UI with backend validation
- Request timeline entries include Gmail rate-limit messaging
- Admin task queue health widget for worker status and queue depth

### v1.0.0 - Current Release (December 2024)

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

Made with care for privacy advocates everywhere.

Remember: Your data is yours. Exercise your rights.
