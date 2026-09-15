# School SaaS Platform

A multi-tenant SaaS platform for schools — managing academics, attendance, learning content, assessments, results, analytics, and fee collection.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Mobile App | Flutter 3.x (Android/iOS) |
| Web App | React 18 + TypeScript |
| Backend | FastAPI + Python 3.11 |
| ORM | SQLModel |
| Auth | FastAPI-Users (JWT) |
| Database | PostgreSQL 15 |
| Storage | Cloudflare R2 (S3-compatible) |

## Project Structure

```
school-saas-platform/
├── backend/          # FastAPI backend
├── mobile/           # Flutter student app
├── web/              # React web app (Teacher + Management)
├── docs/             # Documentation
└── docker-compose.yml
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for web frontend)
- Flutter 3.x (for mobile app)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/balasukumarTR/school-saas-platform.git
   cd school-saas-platform
   ```

2. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Backend Development (without Docker)

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

### Run Tests

```bash
cd backend
poetry run pytest
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## User Roles

| Role | Access |
|------|--------|
| **Student** | Own profile, attendance, subjects, lessons, results |
| **Teacher** | Assigned classes, attendance entry, lessons, results entry |
| **Management** | Full school access, student/teacher management, fees |

## Documentation

- [Architecture](docs/architecture/01_FINAL_ARCHITECTURE.md)
- [API Reference](docs/api.md)
- [Database Schema](docs/database.md)
- [Deployment Guide](docs/deployment.md)

## License

Proprietary - All rights reserved.
