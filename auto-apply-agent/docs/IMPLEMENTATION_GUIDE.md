# AutoApply Agent - Intelligent Job Application System

A full-stack AI-powered job application agent that automatically finds, tailors, and submits job applications on your behalf. Built with a modern tech stack featuring React frontend, FastAPI backend, AI-driven RAG system, and persistent database storage.

## 🚀 Features

- **Automated Job Collection**: Aggregates jobs from Adzuna, Jooble, YC Startups, and RSS feeds
- **AI-Powered RAG**: Zero-hallucination application content using your verified experience
- **Smart Application Engine**: 
  - Headless browser automation for web forms (Lever, Greenhouse, Workday)
  - Direct email applications for contact-based roles
  - LinkedIn Easy Apply support
- **Multi-Model Fallback**: Groq → OpenRouter → HuggingFace automatic retry system
- **Real-Time Dashboard**: Monitor applications, success rates, and pending actions
- **Persistent Storage**: PostgreSQL database with full audit trails
- **Resume Management**: Multiple resume versions for different role types

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI Backend│────▶│  PostgreSQL DB  │
│   (Frontend)    │◀────│   (REST API)     │◀────│  (Persistence)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   AI Services    │
                        │  - Groq          │
                        │  - OpenRouter    │
                        │  - HuggingFace   │
                        └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │ Browser Automation│
                        │  - Playwright    │
                        │  - Browserless   │
                        └──────────────────┘
```

## 📁 Project Structure

```
auto-apply-agent/
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/           # API route definitions
│   │   ├── routers/       # Route handlers
│   │   ├── services/      # Business logic (AI, browser, jobs)
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── utils/         # Helpers, prompts, validators
│   │   └── main.py        # Application entry point
│   ├── tests/             # Pytest test suite
│   └── requirements.txt   # Python dependencies
├── frontend/              # React + TypeScript application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API client services
│   │   ├── store/         # State management (Zustand)
│   │   └── types/         # TypeScript type definitions
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
├── database/              # Database initialization scripts
├── migrations/            # Alembic database migrations
├── config/                # Configuration files
├── resumes/               # User resume PDFs
├── context/               # Personal data JSON for RAG
├── docs/                  # Documentation
├── docker-compose.yml     # Full stack orchestration
└── .env.example           # Environment variables template
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0 + AsyncIO
- **Task Queue**: Celery + Redis (for background job processing)
- **Browser Automation**: Playwright + Browserless
- **AI Integration**: LangChain-compatible adapters

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand
- **HTTP Client**: TanStack Query (React Query)
- **Charts**: Recharts

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Traefik (optional)
- **Monitoring**: Prometheus + Grafana (optional)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- API Keys: Adzuna, Groq/OpenRouter

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd auto-apply-agent
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5432

### Manual Setup (Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Database:**
```bash
docker-compose up -d postgres redis
alembic upgrade head
```

## 📊 Core Modules

### 1. Job Scout Service
- Polls multiple job APIs (Adzuna, Jooble, RSS feeds)
- Filters by keywords, location, salary range
- Detects ATS platforms (Lever, Greenhouse, Workday)
- Calculates match scores based on your skills

### 2. RAG Engine
- Loads personal data from `context/personal_data.json`
- Retrieves relevant experience for each job description
- Generates tailored cover letters and responses
- Enforces zero-hallucination constraints

### 3. Application Executor
- **Web Form Path**: Uses Playwright to navigate, fill, and submit
- **Email Path**: Sends customized emails via SMTP/Gmail API
- **LinkedIn Path**: Automates Easy Apply submissions
- Verifies successful submission with screenshot/text confirmation

### 4. Fallback System
- Primary: Groq (fastest, free tier)
- Fallback 1: OpenRouter (model routing)
- Fallback 2: HuggingFace Inference API
- Automatic retry on rate limits or errors

## 🔐 Security

- Environment variables for all secrets
- JWT authentication for API access
- CORS configuration for frontend
- Input validation and sanitization
- Rate limiting on API endpoints
- Encrypted storage for sensitive data

## 📈 Monitoring & Analytics

- Application success/failure rates
- Time-to-apply metrics
- Model performance comparison
- Cost tracking per application
- Error logging and alerting

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests
cd frontend
npm test

# End-to-end tests
docker-compose -f docker-compose.test.yml up
```

## 📝 Configuration

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/autoapply

# AI Providers
GROQ_API_KEY=your_key
OPENROUTER_API_KEY=your_key
HUGGINGFACE_TOKEN=your_token

# Job APIs
ADZUNA_APP_ID=your_id
ADZUNA_API_KEY=your_key

# Browser Automation
BROWSERLESS_URL=http://browserless:3000

# Email (for direct applications)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your_email
SMTP_PASSWORD=your_app_password

# Application Settings
MAX_DAILY_APPLICATIONS=20
RETRY_ATTEMPTS=3
MATCH_SCORE_THRESHOLD=0.7
```

## 🎯 Usage Workflow

1. **Onboarding**: Upload resume, configure preferences, add personal data
2. **Job Discovery**: System collects matching jobs hourly
3. **Review Dashboard**: Approve/reject suggested applications
4. **Auto-Apply**: System executes applications with AI assistance
5. **Track Progress**: Monitor status, interviews, and outcomes

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Inspired by LoopCV and the open-source job automation community.

---

**Built with ❤️ for job seekers in tech**
