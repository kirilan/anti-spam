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

### 📊 **Response Tracking & Analytics**
- Automatic detection of broker responses
- Classify responses: confirmation, rejection, acknowledgment, info request
- Daily automated scans for new responses (Celery Beat scheduling)
- Success rate analytics and broker compliance ranking
- Timeline charts showing request progress over time

### 📈 **Interactive Dashboard**
- Real-time overview of all deletion activities
- Success rate metrics and confirmation tracking
- Recent broker responses with type badges
- Quick action shortcuts to key features

### 🎯 **Advanced Analytics**
- Visual charts with recharts library
- Broker compliance ranking (success rate + response time)
- Response type distribution pie charts
- Timeline views (7/30/90 day ranges)
- Average response time tracking

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
  - OR **Python 3.11+**, **Node.js 20+**, **PostgreSQL 15**, **Redis 7**
- **Google Cloud Project** with Gmail API enabled
- **Gmail Account** for testing

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/data-deletion-assistant.git
cd data-deletion-assistant
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

# Environment
ENVIRONMENT=development
VITE_API_URL=http://localhost:8000
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

## 🗺️ Roadmap

### 🎯 Near-term Enhancements (v1.1)

**Core Features**
- [ ] Authorization document generation (proof of identity for deletion requests)
- [ ] Custom email template editor for deletion requests
- [ ] Bulk deletion request creation (select multiple brokers at once)
- [ ] Email preview improvements with syntax highlighting
- [ ] Request notes and attachment support
- [ ] Manual response classification override

**User Experience**
- [ ] Advanced filtering and search (by date, broker, status)
- [ ] Sorting options for all list views
- [ ] Pagination for large datasets
- [ ] Dark mode theme
- [ ] Keyboard shortcuts for common actions
- [ ] Toast notifications for async operations

**Data & Reporting**
- [ ] Export deletion history to CSV/JSON
- [ ] Export analytics reports to PDF
- [ ] Data backup and restore functionality
- [ ] Request timeline visualization
- [ ] Email activity heatmap

### 🚀 Medium-term Features (v1.5)

**Intelligence & Automation**
- [ ] Machine learning-based email classification (replace keyword matching)
- [ ] AI-powered broker detection from email content
- [ ] Smart response parsing for unstructured replies
- [ ] Automated follow-up reminders (7, 14, 30 day intervals)
- [ ] Duplicate detection for broker emails
- [ ] Suggested actions based on response patterns

**Integrations**
- [ ] Integration with other email providers (Outlook, Yahoo, ProtonMail)
- [ ] Webhook notifications for status changes
- [ ] Zapier/Make.com integration
- [ ] Calendar integration for follow-up scheduling
- [ ] Slack/Discord notifications

**Multi-user & Collaboration**
- [ ] Multi-user support with role-based access
- [ ] Admin dashboard for instance management
- [ ] Team workspaces for shared deletion campaigns
- [ ] Activity logs and audit trails
- [ ] User invitation system

### 🌟 Long-term Vision (v2.0)

**Platform Extensions**
- [ ] Mobile app (React Native for iOS/Android)
- [ ] Browser extension for quick deletion requests
- [ ] Desktop app (Electron)
- [ ] REST API with authentication for third-party integrations
- [ ] GraphQL API option

**Community & Data**
- [ ] Community-contributed broker database
- [ ] Crowdsourced response templates
- [ ] Broker compliance leaderboard (public)
- [ ] Share success stories anonymously
- [ ] Data broker discovery from user submissions

**Advanced Features**
- [ ] Multi-language support (Spanish, French, German, Portuguese, Italian)
- [ ] Regional compliance (GDPR, CCPA, PIPEDA, LGPD)
- [ ] Automated identity verification with document upload
- [ ] Legal template library (state-specific)
- [ ] Request escalation workflow (from email → legal action)
- [ ] Integration with legal services for complex cases

**Technical Improvements**
- [ ] Real-time updates with WebSockets
- [ ] Advanced rate limiting and API throttling
- [ ] Multi-tenant architecture
- [ ] Horizontal scaling with Kubernetes
- [ ] Comprehensive test suite (unit, integration, e2e)
- [ ] Performance monitoring and alerting
- [ ] Database query optimization
- [ ] Redis caching for frequently accessed data

---

**Made with ❤️ for privacy advocates everywhere**

*Remember: Your data is yours. Exercise your rights.* 🛡️
