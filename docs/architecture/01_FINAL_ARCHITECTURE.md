# School SaaS Platform — Final Architecture

**Date:** 2026-09-15  
**Status:** APPROVED  
**Approach:** Path 2 — Custom auth, easy AWS migration later

---

## 1. Finalized Technology Stack

### Overview

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Mobile App** | Flutter 3.x | Cross-platform (Android/iOS), single codebase |
| **Web App** | React 18 + TypeScript | One app for Teachers + Management (role-based) |
| **Backend** | FastAPI + Python 3.11 | Modern, async, auto-documentation |
| **ORM** | SQLModel | Combines SQLAlchemy + Pydantic, less boilerplate |
| **Auth** | FastAPI-Users | Battle-tested, no vendor lock-in, easy AWS migration |
| **Database** | PostgreSQL 15 | Standard, migrates cleanly to AWS RDS |
| **File Storage** | Cloudflare R2 | S3-compatible, 10GB free, easy migrate to AWS S3 |
| **Backend Hosting** | Railway | Simple deploys, $10-15/month |
| **DB Hosting** | Neon (or Railway PG) | Free tier, serverless PostgreSQL |
| **Web Hosting** | Vercel | Free, automatic deploys |
| **DNS/CDN** | Cloudflare | Free SSL, DDoS protection |

### Cost Summary

| Environment | Monthly Cost |
|-------------|--------------|
| **Development** | $0 (local Docker) |
| **Pilot (300 students)** | $20-40 |
| **Growth (1000+ students)** | $50-100 |
| **Scale (AWS migration)** | $200-500 |

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                     │
├─────────────────────────┬───────────────────────────────────────────────┤
│      Flutter App        │              React Web App                     │
│      (Students)         │         (Teachers + Management)                │
│      Android / iOS      │           Role-based routing                   │
└───────────┬─────────────┴─────────────────┬─────────────────────────────┘
            │                               │
            │          HTTPS                │
            └───────────────┬───────────────┘
                            ▼
                   ┌─────────────────┐
                   │   Cloudflare    │
                   │   (DNS + CDN)   │
                   └────────┬────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
   ┌─────────────────┐             ┌─────────────────┐
   │     Railway     │             │     Vercel      │
   │  FastAPI Backend│             │   React Web     │
   │                 │             │                 │
   │ ┌─────────────┐ │             └─────────────────┘
   │ │ FastAPI-    │ │
   │ │ Users Auth  │ │
   │ └─────────────┘ │
   │ ┌─────────────┐ │
   │ │  SQLModel   │ │
   │ │    ORM      │ │
   │ └─────────────┘ │
   └────────┬────────┘
            │
     ┌──────┴──────┐
     │             │
     ▼             ▼
┌─────────┐  ┌─────────────┐
│  Neon   │  │ Cloudflare  │
│PostgreSQL│  │     R2      │
│         │  │  (Storage)  │
└─────────┘  └─────────────┘


═══════════════════════════════════════════════════════════════════════════
                        FUTURE AWS MIGRATION PATH
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│                              AWS                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Railway ──────────────────────────────► ECS Fargate                   │
│   (same Docker image, redeploy)                                          │
│                                                                          │
│   Neon PostgreSQL ──────────────────────► RDS PostgreSQL                │
│   (pg_dump / pg_restore)                                                 │
│                                                                          │
│   Cloudflare R2 ────────────────────────► S3                            │
│   (S3-compatible, aws s3 sync)                                           │
│                                                                          │
│   Vercel ───────────────────────────────► CloudFront + S3               │
│   (build & upload static files)                                          │
│                                                                          │
│   FastAPI-Users Auth ───────────────────► Same code (no changes)        │
│   (stored in your PostgreSQL)                                            │
│                                                                          │
│   Migration effort: ~1 week                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Project Structure

```
school-saas-platform/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml                 # Local development
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml                 # Dependencies (Poetry)
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── config.py                  # Settings (pydantic-settings)
│   │   ├── database.py                # SQLModel engine setup
│   │   │
│   │   ├── models/                    # SQLModel models (DB + Pydantic combined)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Base model with common fields
│   │   │   ├── school.py
│   │   │   ├── user.py                # FastAPI-Users compatible
│   │   │   ├── student.py
│   │   │   ├── teacher.py
│   │   │   ├── academic.py            # Classes, sections, subjects
│   │   │   ├── attendance.py
│   │   │   ├── syllabus.py
│   │   │   ├── lesson.py
│   │   │   ├── content.py
│   │   │   ├── exam.py
│   │   │   ├── fee.py
│   │   │   └── audit.py
│   │   │
│   │   ├── schemas/                   # Additional Pydantic schemas (API-specific)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── dashboard.py
│   │   │   └── reports.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                # Dependencies (get_current_user, etc.)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py          # Main router combining all
│   │   │       ├── auth.py            # FastAPI-Users routes
│   │   │       ├── students.py
│   │   │       ├── teachers.py
│   │   │       ├── management.py
│   │   │       ├── attendance.py
│   │   │       ├── lessons.py
│   │   │       ├── results.py
│   │   │       ├── fees.py
│   │   │       └── content.py
│   │   │
│   │   ├── services/                  # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── student.py
│   │   │   ├── teacher.py
│   │   │   ├── attendance.py
│   │   │   ├── fee.py
│   │   │   └── storage.py             # R2/S3 operations
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py            # FastAPI-Users setup
│   │   │   ├── permissions.py         # RBAC decorators
│   │   │   └── tenancy.py             # Multi-tenant helpers
│   │   │
│   │   └── utils/
│   │       └── __init__.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_students.py
│       ├── test_rbac.py
│       └── test_tenant_isolation.py
│
├── mobile/                            # Flutter student app
│   ├── pubspec.yaml
│   ├── lib/
│   │   ├── main.dart
│   │   ├── config/
│   │   │   ├── api_config.dart
│   │   │   ├── theme.dart
│   │   │   └── routes.dart
│   │   ├── models/
│   │   ├── services/
│   │   │   ├── api_service.dart
│   │   │   ├── auth_service.dart
│   │   │   └── storage_service.dart
│   │   ├── providers/
│   │   ├── screens/
│   │   │   ├── splash/
│   │   │   ├── login/
│   │   │   ├── dashboard/
│   │   │   ├── attendance/
│   │   │   ├── subjects/
│   │   │   ├── lessons/
│   │   │   ├── results/
│   │   │   └── profile/
│   │   └── widgets/
│   ├── android/
│   ├── ios/
│   └── test/
│
├── web/                               # React app (Teachers + Management)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   ├── client.ts              # Axios/fetch setup
│   │   │   └── types.ts               # Generated from OpenAPI
│   │   ├── components/
│   │   │   ├── ui/                    # Base components
│   │   │   └── shared/                # App-specific shared
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   ├── teacher/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── Classes.tsx
│   │   │   │   ├── Attendance.tsx
│   │   │   │   ├── Lessons.tsx
│   │   │   │   └── Results.tsx
│   │   │   └── management/
│   │   │       ├── Dashboard.tsx
│   │   │       ├── Students.tsx
│   │   │       ├── Teachers.tsx
│   │   │       ├── Classes.tsx
│   │   │       ├── Fees.tsx
│   │   │       ├── Reports.tsx
│   │   │       └── Settings.tsx
│   │   ├── hooks/
│   │   ├── stores/                    # Zustand or React Query
│   │   └── utils/
│   └── tests/
│
├── docs/
│   ├── architecture/
│   │   ├── 00_ARCHITECTURE_PROPOSAL.md
│   │   └── 01_FINAL_ARCHITECTURE.md   # This document
│   ├── api.md
│   ├── database.md
│   └── deployment.md
│
└── .github/
    └── workflows/
        ├── backend-ci.yml
        ├── mobile-ci.yml
        └── web-ci.yml
```

---

## 4. Database Schema (Core Tables)

Using SQLModel — models serve as both database tables AND Pydantic schemas.

### 4.1 Multi-Tenancy

```python
# Every tenant-scoped table includes school_id
class School(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    code: str = Field(unique=True)  # e.g., "SJPS"
    logo_url: str | None = None
    settings: dict = Field(default_factory=dict, sa_column=Column(JSON))
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.2 Users & Auth (FastAPI-Users Compatible)

```python
class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    school_id: uuid.UUID = Field(foreign_key="school.id")
    email: str = Field(unique=True, index=True)
    hashed_password: str
    first_name: str
    last_name: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserRole(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    role: str  # "student", "teacher", "management"
```

### 4.3 Core Entities

```
schools
├── users (FastAPI-Users)
│   ├── user_roles
│   ├── students (extends user)
│   └── teachers (extends user)
├── academic_years
├── classes
│   └── sections
│       └── student_enrollments
├── subjects
│   └── class_subjects (teacher assignments)
├── attendance_records
├── syllabus
│   └── syllabus_topics
│       └── lessons
│           └── learning_content
├── exams
│   └── exam_subjects
│       └── student_results
├── fee_structures
│   └── student_fee_accounts
│       ├── fee_payments (immutable)
│       └── fee_adjustments
├── learning_events (analytics)
└── audit_logs
```

---

## 5. Authentication Flow

Using **FastAPI-Users** with JWT strategy:

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Client     │         │   FastAPI    │         │  PostgreSQL  │
│ (Flutter/Web)│         │   Backend    │         │              │
└──────┬───────┘         └──────┬───────┘         └──────┬───────┘
       │                        │                        │
       │  POST /auth/login      │                        │
       │  {email, password}     │                        │
       │───────────────────────>│                        │
       │                        │  Query user by email   │
       │                        │───────────────────────>│
       │                        │                        │
       │                        │  User record           │
       │                        │<───────────────────────│
       │                        │                        │
       │                        │  Verify password hash  │
       │                        │  (Argon2id)            │
       │                        │                        │
       │  {access_token,        │                        │
       │   refresh_token}       │                        │
       │<───────────────────────│                        │
       │                        │                        │
       │  GET /students/me      │                        │
       │  Authorization: Bearer │                        │
       │───────────────────────>│                        │
       │                        │  Decode JWT            │
       │                        │  Extract user_id       │
       │                        │  Check school_id       │
       │                        │───────────────────────>│
       │                        │                        │
       │  {student data}        │  Student data          │
       │<───────────────────────│<───────────────────────│
```

### Token Configuration

| Token | Lifetime | Storage |
|-------|----------|---------|
| Access Token (JWT) | 30 minutes | Client memory |
| Refresh Token | 7 days | HttpOnly cookie or secure storage |

---

## 6. API Endpoints Summary

### Auth (FastAPI-Users provides these)
```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout  
POST   /api/v1/auth/refresh
POST   /api/v1/auth/register        # Management creates users
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
```

### Student APIs
```
GET    /api/v1/students/me
GET    /api/v1/students/me/dashboard
GET    /api/v1/students/me/attendance
GET    /api/v1/students/me/subjects
GET    /api/v1/students/me/syllabus
GET    /api/v1/students/me/lessons
GET    /api/v1/students/me/lessons/{id}
GET    /api/v1/students/me/results
PUT    /api/v1/students/me/profile
```

### Teacher APIs
```
GET    /api/v1/teachers/me
GET    /api/v1/teachers/me/dashboard
GET    /api/v1/teachers/me/classes
GET    /api/v1/teachers/me/classes/{id}/students
POST   /api/v1/teachers/attendance
GET    /api/v1/teachers/me/lessons
POST   /api/v1/teachers/me/lessons
POST   /api/v1/teachers/me/content/upload-url
POST   /api/v1/teachers/me/results
```

### Management APIs
```
GET    /api/v1/management/dashboard
GET    /api/v1/management/students
POST   /api/v1/management/students
GET    /api/v1/management/teachers
POST   /api/v1/management/teachers
GET    /api/v1/management/fees/dashboard
GET    /api/v1/management/fees/students/{id}
POST   /api/v1/management/fees/payments
GET    /api/v1/management/analytics
```

---

## 7. Development Phases

### Phase 1: Foundation (Weeks 1-2)
- [x] Architecture finalized
- [ ] Project structure created
- [ ] Backend scaffolding (FastAPI + SQLModel)
- [ ] Database models (User, School, Student)
- [ ] FastAPI-Users authentication
- [ ] Flutter app scaffolding
- [ ] Login screen + API integration
- [ ] Student dashboard (basic)

**Success Criterion:** Student logs in via Flutter, sees their name from PostgreSQL.

### Phase 2: Academic Core (Weeks 3-5)
- [ ] Classes, Sections, Subjects models
- [ ] Student enrollment
- [ ] Attendance module
- [ ] Syllabus + Lessons
- [ ] Content storage (R2)
- [ ] Teacher web portal (React)

### Phase 3: Results & Fees (Weeks 6-9)
- [ ] Exams + Results
- [ ] Fee management
- [ ] Management portal
- [ ] Reports

### Phase 4: Polish & Deploy (Weeks 10-12)
- [ ] Testing
- [ ] Railway deployment
- [ ] Pilot launch

---

## 8. Open Items (Answered)

| Question | Decision |
|----------|----------|
| Repository | `school-saas-platform` under `balasukumarTR` |
| Data residency | Not required — can use any region |
| Auth approach | FastAPI-Users (custom, no vendor lock-in) |
| Infrastructure | Railway + Neon + R2 → AWS later |
| Budget | ~$20-40/month for pilot |
| Migration path | ~1 week to AWS when scaling |

---

## 9. Next Steps

1. Create GitHub repository
2. Set up backend project with FastAPI + SQLModel + FastAPI-Users
3. Create database models and initial migration
4. Implement authentication endpoints
5. Set up Flutter app with login flow
6. Connect Flutter to backend

---

*Document version: 2.0 (Final)*  
*Last updated: 2026-09-15*
