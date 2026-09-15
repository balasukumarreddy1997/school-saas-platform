# School SaaS Platform — Architecture Proposal

**Date:** 2026-09-15  
**Status:** AWAITING APPROVAL  
**Target:** St Joseph's Public School (pilot), multi-school SaaS

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Technology Decisions](#3-technology-decisions)
4. [Database Design](#4-database-design)
5. [Folder Structure](#5-folder-structure)
6. [Authentication Design](#6-authentication-design)
7. [RBAC Design](#7-rbac-design)
8. [Multi-Tenant Design](#8-multi-tenant-design)
9. [API Structure](#9-api-structure)
10. [AWS Deployment Architecture](#10-aws-deployment-architecture)
11. [Development Roadmap](#11-development-roadmap)
12. [Security Considerations](#12-security-considerations)
13. [Open Questions](#13-open-questions)

---

## 1. Executive Summary

This document proposes the architecture for a production-quality, multi-tenant SaaS platform for schools. The platform will serve three user roles (Student, Teacher, Management) and handle academics, attendance, learning content, assessments, results, analytics, and fee collection.

**Key characteristics:**
- Multi-tenant from day one (school isolation at database level)
- Modular monolith backend (FastAPI + PostgreSQL)
- Flutter mobile app for students
- React web portals for teachers and management
- AWS infrastructure (cost-conscious, no Kubernetes for V1)
- 12-week timeline to production pilot (100-300 students)

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
├─────────────────┬─────────────────────┬─────────────────────────────────────┤
│  Flutter App    │   Teacher Portal    │      Management Portal              │
│  (Android/iOS)  │   (React Web)       │      (React Web)                    │
│  Students       │   Teachers          │      Administrators                 │
└────────┬────────┴──────────┬──────────┴──────────────┬──────────────────────┘
         │                   │                         │
         └───────────────────┼─────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AWS CLOUDFRONT (CDN)                                 │
│                    Static assets + Video delivery                            │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWS WAF                                            │
│                    Rate limiting, SQL injection protection                   │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LOAD BALANCER                                 │
│                         (HTTPS termination)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ECS FARGATE / EC2                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      FastAPI Application                               │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│  │  │  Auth   │ │ Users   │ │Students │ │Teachers │ │ Classes │        │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│  │  │Attendance│ │Syllabus │ │Lessons  │ │Results  │ │  Fees   │        │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                                │  │
│  │  │Analytics│ │ Content │ │  Audit  │                                │  │
│  │  └─────────┘ └─────────┘ └─────────┘                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
         │                              │                         │
         ▼                              ▼                         ▼
┌─────────────────┐          ┌─────────────────┐       ┌─────────────────────┐
│  RDS PostgreSQL │          │     AWS S3      │       │   AWS Secrets       │
│  (Multi-tenant) │          │ Videos/Content  │       │     Manager         │
└─────────────────┘          └─────────────────┘       └─────────────────────┘
         │
         ▼
┌─────────────────┐
│   CloudWatch    │
│ Logs & Metrics  │
└─────────────────┘
```

### 2.2 Data Flow

1. **Student opens Flutter app** → CloudFront → WAF → ALB → FastAPI → PostgreSQL
2. **Teacher uploads video** → FastAPI generates presigned URL → Direct upload to S3
3. **Student watches video** → CloudFront (signed URL) → S3
4. **Management views analytics** → FastAPI aggregates from PostgreSQL → Returns JSON

---

## 3. Technology Decisions

### 3.1 Backend

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | Strong ecosystem, fast development, good for data/analytics |
| Framework | FastAPI | Modern, async, automatic OpenAPI docs, Pydantic validation |
| ORM | SQLAlchemy 2.0 | Mature, well-documented, async support |
| Migrations | Alembic | Standard for SQLAlchemy, version-controlled migrations |
| Validation | Pydantic v2 | Automatic validation, serialization, OpenAPI schema generation |
| Testing | pytest + pytest-asyncio | Standard Python testing with async support |
| Task Queue | None for V1 | Add Celery + Redis later if needed for background jobs |

### 3.2 Database

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Primary DB | PostgreSQL 15+ | ACID compliance, JSON support, proven at scale |
| Hosting | AWS RDS | Managed backups, Multi-AZ available, no ops overhead |
| Connection Pool | SQLAlchemy + asyncpg | Async connections, connection pooling built-in |

### 3.3 Frontend — Mobile

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | Flutter 3.x | Cross-platform (Android/iOS), single codebase |
| State | Riverpod or Provider | Simple, testable state management |
| HTTP | Dio | Interceptors for auth, retry logic |
| Local Storage | Hive or shared_preferences | Offline caching, secure token storage |

### 3.4 Frontend — Web

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | React 18 + TypeScript | Industry standard, large talent pool |
| UI Library | Tailwind CSS + shadcn/ui | Fast development, consistent design |
| State | React Query (TanStack) | Server state management, caching |
| Routing | React Router v6 | Standard routing solution |
| Build | Vite | Fast builds, modern tooling |

### 3.5 Infrastructure

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Compute | ECS Fargate (or EC2) | Simpler than EKS, cost-effective for V1 |
| CDN | CloudFront | Video delivery, static assets, global edge |
| Storage | S3 | Videos, documents, learning materials |
| Load Balancer | ALB | Path-based routing, HTTPS termination |
| WAF | AWS WAF | Rate limiting, SQL injection, XSS protection |
| Secrets | AWS Secrets Manager | Rotate credentials, no secrets in code |
| DNS | Route 53 | Managed DNS, health checks |
| Monitoring | CloudWatch | Logs, metrics, alarms |
| IaC | AWS CDK (Python) | Type-safe, testable infrastructure code |

### 3.6 Decisions NOT Made for V1

- **No Kubernetes/EKS** — Complexity not justified for pilot scale
- **No Kafka/event streaming** — Synchronous APIs sufficient initially
- **No microservices** — Modular monolith is simpler to develop/deploy
- **No Redis** — Add later if caching/sessions/queues needed
- **No AI features** — Architecture supports future addition

---

## 4. Database Design

### 4.1 Entity Relationship Diagram (Core Tables)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MULTI-TENANCY LAYER                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┐
│    schools    │  (Tenant table - every other table references this)
├───────────────┤
│ id (UUID, PK) │
│ name          │
│ code          │  (unique short code, e.g., "SJPS")
│ logo_url      │
│ address       │
│ contact_email │
│ contact_phone │
│ settings      │  (JSONB - school-specific config)
│ is_active     │
│ created_at    │
│ updated_at    │
└───────┬───────┘
        │
        │ 1:N
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER DOMAIN                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────┐         ┌───────────────────┐
│       users       │         │    user_roles     │
├───────────────────┤         ├───────────────────┤
│ id (UUID, PK)     │────────▶│ id (UUID, PK)     │
│ school_id (FK)    │         │ user_id (FK)      │
│ email             │         │ role              │  (student/teacher/management)
│ phone             │         │ created_at        │
│ password_hash     │         └───────────────────┘
│ first_name        │
│ last_name         │         A user can have multiple roles (rare but possible)
│ is_active         │
│ last_login_at     │
│ created_at        │
│ updated_at        │
└───────────────────┘

┌───────────────────┐         ┌───────────────────┐
│     students      │         │     teachers      │
├───────────────────┤         ├───────────────────┤
│ id (UUID, PK)     │         │ id (UUID, PK)     │
│ user_id (FK)      │         │ user_id (FK)      │
│ school_id (FK)    │         │ school_id (FK)    │
│ admission_number  │         │ employee_id       │
│ roll_number       │         │ department        │
│ date_of_birth     │         │ qualification     │
│ gender            │         │ date_of_joining   │
│ blood_group       │         │ is_class_teacher  │
│ parent_name       │         │ created_at        │
│ parent_phone      │         │ updated_at        │
│ address           │         └─────────┬─────────┘
│ created_at        │                   │
│ updated_at        │                   │
└─────────┬─────────┘                   │
          │                             │
          │                             │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ACADEMIC STRUCTURE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────┐
│ academic_years    │
├───────────────────┤
│ id (UUID, PK)     │
│ school_id (FK)    │
│ name              │  (e.g., "2026-2027")
│ start_date        │
│ end_date          │
│ is_current        │
│ created_at        │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐         ┌───────────────────┐
│     classes       │         │     sections      │
├───────────────────┤         ├───────────────────┤
│ id (UUID, PK)     │◀────────│ id (UUID, PK)     │
│ school_id (FK)    │         │ class_id (FK)     │
│ academic_year_id  │         │ name              │  (A, B, C...)
│ name              │  (1-12) │ capacity          │
│ grade_level       │         │ class_teacher_id  │  (FK to teachers)
│ created_at        │         │ created_at        │
└───────────────────┘         └─────────┬─────────┘
                                        │
                                        ▼
┌───────────────────┐         ┌───────────────────────────┐
│     subjects      │         │  student_enrollments      │
├───────────────────┤         ├───────────────────────────┤
│ id (UUID, PK)     │         │ id (UUID, PK)             │
│ school_id (FK)    │         │ student_id (FK)           │
│ name              │         │ section_id (FK)           │
│ code              │         │ academic_year_id (FK)     │
│ description       │         │ roll_number               │
│ is_active         │         │ enrollment_date           │
│ created_at        │         │ status                    │  (active/transferred/graduated)
└───────────────────┘         │ created_at                │
                              └───────────────────────────┘

┌───────────────────────────┐
│    class_subjects         │  (Which subjects are taught in which class)
├───────────────────────────┤
│ id (UUID, PK)             │
│ class_id (FK)             │
│ subject_id (FK)           │
│ teacher_id (FK)           │  (Teacher assigned to this subject for this class)
│ periods_per_week          │
│ created_at                │
└───────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              ATTENDANCE                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────┐
│    attendance_records     │
├───────────────────────────┤
│ id (UUID, PK)             │
│ student_id (FK)           │
│ section_id (FK)           │
│ date                      │
│ status                    │  (present/absent/late/excused)
│ marked_by (FK to users)   │
│ remarks                   │
│ created_at                │
│ updated_at                │
└───────────────────────────┘
  UNIQUE(student_id, date)

┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYLLABUS & CONTENT                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────┐         ┌───────────────────────────┐
│    syllabus               │         │    syllabus_topics        │
├───────────────────────────┤         ├───────────────────────────┤
│ id (UUID, PK)             │◀────────│ id (UUID, PK)             │
│ school_id (FK)            │         │ syllabus_id (FK)          │
│ class_id (FK)             │         │ chapter_number            │
│ subject_id (FK)           │         │ chapter_name              │
│ academic_year_id (FK)     │         │ topic_name                │
│ description               │         │ description               │
│ created_at                │         │ sequence_order            │
│ updated_at                │         │ estimated_hours           │
└───────────────────────────┘         │ created_at                │
                                      └─────────────┬─────────────┘
                                                    │
                                                    ▼
┌───────────────────────────┐         ┌───────────────────────────┐
│    lessons                │         │    learning_content       │
├───────────────────────────┤         ├───────────────────────────┤
│ id (UUID, PK)             │◀────────│ id (UUID, PK)             │
│ syllabus_topic_id (FK)    │         │ lesson_id (FK)            │
│ title                     │         │ content_type              │  (video/pdf/image/doc)
│ description               │         │ title                     │
│ learning_objectives       │         │ file_url                  │  (S3 URL)
│ sequence_order            │         │ file_size_bytes           │
│ duration_minutes          │         │ duration_seconds          │  (for videos)
│ created_by (FK)           │         │ thumbnail_url             │
│ is_published              │         │ sequence_order            │
│ created_at                │         │ created_by (FK)           │
│ updated_at                │         │ created_at                │
└───────────────────────────┘         └───────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           ASSESSMENTS & RESULTS                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────┐         ┌───────────────────────────┐
│    exams                  │         │    exam_subjects          │
├───────────────────────────┤         ├───────────────────────────┤
│ id (UUID, PK)             │◀────────│ id (UUID, PK)             │
│ school_id (FK)            │         │ exam_id (FK)              │
│ academic_year_id (FK)     │         │ subject_id (FK)           │
│ name                      │         │ max_marks                 │
│ exam_type                 │         │ passing_marks             │
│ start_date                │         │ exam_date                 │
│ end_date                  │         │ created_at                │
│ is_published              │         └─────────────┬─────────────┘
│ created_at                │                       │
└───────────────────────────┘                       ▼
                                      ┌───────────────────────────┐
                                      │    student_results        │
                                      ├───────────────────────────┤
                                      │ id (UUID, PK)             │
                                      │ student_id (FK)           │
                                      │ exam_subject_id (FK)      │
                                      │ marks_obtained            │
                                      │ grade                     │
                                      │ remarks                   │
                                      │ entered_by (FK)           │
                                      │ created_at                │
                                      │ updated_at                │
                                      └───────────────────────────┘
                                        UNIQUE(student_id, exam_subject_id)

┌─────────────────────────────────────────────────────────────────────────────┐
│                              FEE MANAGEMENT                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────┐
│    fee_structures         │  (Template: what fees exist for a class)
├───────────────────────────┤
│ id (UUID, PK)             │
│ school_id (FK)            │
│ academic_year_id (FK)     │
│ class_id (FK)             │
│ fee_type                  │  (tuition/transport/lab/library/etc)
│ amount                    │
│ frequency                 │  (annual/monthly/quarterly/one-time)
│ due_date                  │
│ created_at                │
└───────────────────────────┘

┌───────────────────────────┐
│    student_fee_accounts   │  (Each student's fee ledger)
├───────────────────────────┤
│ id (UUID, PK)             │
│ student_id (FK)           │
│ academic_year_id (FK)     │
│ total_fee                 │  (Computed from fee_structures)
│ total_paid                │  (Computed from payments)
│ total_discount            │
│ balance                   │  (total_fee - total_paid - total_discount)
│ created_at                │
│ updated_at                │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│    fee_payments           │  (Immutable transaction log)
├───────────────────────────┤
│ id (UUID, PK)             │
│ student_fee_account_id(FK)│
│ amount                    │
│ payment_date              │
│ payment_method            │  (cash/cheque/online/upi)
│ reference_number          │
│ receipt_number            │
│ notes                     │
│ recorded_by (FK)          │
│ created_at                │
└───────────────────────────┘
  (Never update/delete - corrections go to fee_adjustments)

┌───────────────────────────┐
│    fee_adjustments        │  (For corrections/refunds)
├───────────────────────────┤
│ id (UUID, PK)             │
│ student_fee_account_id(FK)│
│ adjustment_type           │  (discount/waiver/refund/correction)
│ amount                    │  (can be negative)
│ reason                    │
│ reference_payment_id (FK) │  (if correcting a specific payment)
│ approved_by (FK)          │
│ created_at                │
└───────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              ANALYTICS & AUDIT                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────┐
│    learning_events        │  (For analytics)
├───────────────────────────┤
│ id (UUID, PK)             │
│ student_id (FK)           │
│ event_type                │  (login/lesson_view/video_start/video_complete/quiz_attempt)
│ resource_type             │  (lesson/video/quiz)
│ resource_id               │
│ duration_seconds          │
│ metadata                  │  (JSONB - flexible event data)
│ created_at                │
└───────────────────────────┘
  (Partitioned by month for performance)

┌───────────────────────────┐
│    audit_logs             │  (For compliance/debugging)
├───────────────────────────┤
│ id (UUID, PK)             │
│ school_id (FK)            │
│ user_id (FK)              │
│ action                    │  (create/update/delete)
│ entity_type               │  (student/payment/result/etc)
│ entity_id                 │
│ old_values                │  (JSONB)
│ new_values                │  (JSONB)
│ ip_address                │
│ user_agent                │
│ created_at                │
└───────────────────────────┘
  (Partitioned by month, never delete)

┌───────────────────────────┐
│    refresh_tokens         │  (For auth)
├───────────────────────────┤
│ id (UUID, PK)             │
│ user_id (FK)              │
│ token_hash                │
│ device_info               │
│ expires_at                │
│ revoked_at                │
│ created_at                │
└───────────────────────────┘
```

### 4.2 Key Design Decisions

1. **UUIDs as primary keys** — Avoids enumeration attacks, safe for distributed systems
2. **school_id on most tables** — Enables row-level tenant filtering
3. **Soft deletes not used** — Hard delete with audit log instead (simpler)
4. **JSONB for flexible fields** — School settings, event metadata, etc.
5. **Immutable fee_payments** — Financial integrity; corrections use adjustments
6. **Separate student/teacher tables** — Extend user with role-specific data
7. **learning_events partitioned** — Analytics tables grow fast; partition by month

### 4.3 Indexes (Critical)

```sql
-- Tenant isolation (on every tenant-scoped table)
CREATE INDEX idx_students_school_id ON students(school_id);
CREATE INDEX idx_attendance_student_date ON attendance_records(student_id, date);
CREATE INDEX idx_learning_events_student_created ON learning_events(student_id, created_at);
CREATE INDEX idx_fee_payments_account ON fee_payments(student_fee_account_id);
CREATE INDEX idx_audit_logs_school_created ON audit_logs(school_id, created_at);
```

---

## 5. Folder Structure

```
school-saas-platform/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml              # Local development
├── docker-compose.test.yml         # Test environment
│
├── backend/
│   ├── pyproject.toml              # Python dependencies (Poetry)
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── versions/               # Database migrations
│   │   └── env.py
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Settings from env vars
│   │   ├── database.py             # SQLAlchemy setup
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   │
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base model with common fields
│   │   │   ├── school.py
│   │   │   ├── user.py
│   │   │   ├── student.py
│   │   │   ├── teacher.py
│   │   │   ├── academic.py         # Classes, sections, subjects
│   │   │   ├── attendance.py
│   │   │   ├── syllabus.py
│   │   │   ├── lesson.py
│   │   │   ├── content.py
│   │   │   ├── exam.py
│   │   │   ├── result.py
│   │   │   ├── fee.py
│   │   │   ├── analytics.py
│   │   │   └── audit.py
│   │   │
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── student.py
│   │   │   ├── teacher.py
│   │   │   ├── attendance.py
│   │   │   ├── syllabus.py
│   │   │   ├── lesson.py
│   │   │   ├── result.py
│   │   │   ├── fee.py
│   │   │   └── analytics.py
│   │   │
│   │   ├── api/                    # API routes
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Route dependencies
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py       # Combines all routers
│   │   │   │   ├── auth.py
│   │   │   │   ├── students.py
│   │   │   │   ├── teachers.py
│   │   │   │   ├── management.py
│   │   │   │   ├── attendance.py
│   │   │   │   ├── syllabus.py
│   │   │   │   ├── lessons.py
│   │   │   │   ├── results.py
│   │   │   │   ├── fees.py
│   │   │   │   ├── content.py
│   │   │   │   └── analytics.py
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── student.py
│   │   │   ├── teacher.py
│   │   │   ├── attendance.py
│   │   │   ├── fee.py
│   │   │   ├── content.py          # S3 upload/download
│   │   │   └── analytics.py
│   │   │
│   │   ├── core/                   # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── security.py         # Password hashing, JWT
│   │   │   ├── permissions.py      # RBAC logic
│   │   │   ├── tenancy.py          # Multi-tenant helpers
│   │   │   └── exceptions.py       # Custom exceptions
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── s3.py               # S3 utilities
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             # Pytest fixtures
│       ├── test_auth.py
│       ├── test_students.py
│       ├── test_teachers.py
│       ├── test_attendance.py
│       ├── test_fees.py
│       ├── test_tenant_isolation.py
│       └── test_rbac.py
│
├── mobile/                         # Flutter student app
│   ├── pubspec.yaml
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app.dart
│   │   ├── config/
│   │   │   ├── api_config.dart
│   │   │   ├── theme.dart
│   │   │   └── routes.dart
│   │   ├── models/
│   │   ├── services/
│   │   │   ├── api_service.dart
│   │   │   ├── auth_service.dart
│   │   │   └── storage_service.dart
│   │   ├── providers/              # State management
│   │   ├── screens/
│   │   │   ├── splash/
│   │   │   ├── login/
│   │   │   ├── dashboard/
│   │   │   ├── attendance/
│   │   │   ├── subjects/
│   │   │   ├── syllabus/
│   │   │   ├── lessons/
│   │   │   ├── results/
│   │   │   └── profile/
│   │   └── widgets/                # Reusable components
│   ├── android/
│   ├── ios/
│   └── test/
│
├── web-teacher/                    # React teacher portal
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── utils/
│   └── tests/
│
├── web-management/                 # React management portal
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── dashboard/
│   │   │   ├── students/
│   │   │   ├── teachers/
│   │   │   ├── classes/
│   │   │   ├── attendance/
│   │   │   ├── fees/
│   │   │   ├── results/
│   │   │   └── analytics/
│   │   ├── hooks/
│   │   └── utils/
│   └── tests/
│
├── infrastructure/                 # AWS CDK
│   ├── package.json
│   ├── cdk.json
│   ├── lib/
│   │   ├── vpc-stack.ts
│   │   ├── database-stack.ts
│   │   ├── storage-stack.ts
│   │   ├── compute-stack.ts
│   │   ├── cdn-stack.ts
│   │   └── monitoring-stack.ts
│   └── bin/
│       └── infrastructure.ts
│
├── docs/
│   ├── architecture/
│   │   └── 00_ARCHITECTURE_PROPOSAL.md  # This document
│   ├── api.md
│   ├── database.md
│   ├── security.md
│   ├── deployment.md
│   └── development.md
│
└── .github/
    └── workflows/
        ├── backend-ci.yml
        ├── mobile-ci.yml
        ├── web-ci.yml
        └── deploy.yml
```

---

## 6. Authentication Design

### 6.1 Overview

- **Method:** Email/phone + password
- **Tokens:** JWT access token (short-lived) + refresh token (long-lived, stored in DB)
- **Password:** Argon2id hashing (via `passlib`)
- **Session:** Stateless (JWT) with optional token revocation via refresh token table

### 6.2 Token Structure

**Access Token (JWT, 15 min expiry):**
```json
{
  "sub": "user-uuid",
  "school_id": "school-uuid",
  "roles": ["student"],
  "iat": 1694793600,
  "exp": 1694794500
}
```

**Refresh Token (7-30 days, stored in DB):**
- UUID stored in `refresh_tokens` table
- Hashed before storage
- Can be revoked individually or all for a user

### 6.3 Flow

```
1. Login
   POST /auth/login
   Body: { "email": "...", "password": "..." }
   Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }

2. Access Protected Resource
   GET /students/me
   Header: Authorization: Bearer <access_token>

3. Refresh Token
   POST /auth/refresh
   Body: { "refresh_token": "..." }
   Response: { "access_token": "...", "refresh_token": "..." }

4. Logout
   POST /auth/logout
   Body: { "refresh_token": "..." }
   (Revokes the refresh token)

5. Logout All Devices
   POST /auth/logout-all
   (Revokes all refresh tokens for the user)
```

### 6.4 Security Measures

- Passwords hashed with Argon2id (memory-hard, resistant to GPU attacks)
- Access tokens short-lived (15 min) to limit exposure
- Refresh tokens stored hashed, can be revoked
- Failed login tracking (lockout after N attempts) — Phase 2
- Rate limiting on auth endpoints
- No secrets in JWT payload (use user_id to fetch sensitive data)

---

## 7. RBAC Design

### 7.1 Roles

| Role | Description |
|------|-------------|
| `student` | Can view own data only |
| `teacher` | Can view/modify assigned classes' data |
| `management` | Full access within their school |
| `super_admin` | Cross-school access (internal use only, V2) |

### 7.2 Permission Model

Permissions are **implicit based on role + resource ownership**:

```python
# Example permission checks

def can_view_student(current_user, student):
    if current_user.has_role("student"):
        return current_user.student_id == student.id
    if current_user.has_role("teacher"):
        return student in current_user.assigned_students
    if current_user.has_role("management"):
        return current_user.school_id == student.school_id
    return False

def can_record_attendance(current_user, section):
    if current_user.has_role("teacher"):
        return section in current_user.assigned_sections
    if current_user.has_role("management"):
        return current_user.school_id == section.school_id
    return False

def can_access_fees(current_user):
    return current_user.has_role("management")
```

### 7.3 Implementation

```python
# backend/app/core/permissions.py

from enum import Enum
from functools import wraps
from fastapi import HTTPException, status

class Role(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    MANAGEMENT = "management"

def require_roles(*roles: Role):
    """Decorator to check user has at least one of the specified roles."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user, **kwargs):
            user_roles = {r.role for r in current_user.roles}
            if not user_roles.intersection(set(roles)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage in routes:
@router.get("/fees/dashboard")
@require_roles(Role.MANAGEMENT)
async def get_fee_dashboard(current_user: User = Depends(get_current_user)):
    ...
```

### 7.4 Critical Security Rules

1. **Backend enforces ALL permissions** — never trust frontend
2. **Every query filters by school_id** — tenant isolation
3. **Teachers only access assigned classes** — scope check in service layer
4. **Students only access own data** — WHERE student_id = current_user.student_id
5. **Fee module is management-only** — explicit role check
6. **Audit log all sensitive operations** — who did what when

---

## 8. Multi-Tenant Design

### 8.1 Strategy: Shared Database, Shared Schema

All schools share one database with tenant isolation via `school_id` column.

**Why this approach:**
- Simpler operations (one database to backup/monitor)
- Cost-effective for pilot scale
- Easy to add schools
- Can migrate to separate schemas/databases later if needed

### 8.2 Implementation

```python
# backend/app/core/tenancy.py

from sqlalchemy.orm import Query
from fastapi import Request

class TenantMiddleware:
    """Middleware that extracts school_id from JWT and sets it in request state."""
    
    async def __call__(self, request: Request, call_next):
        # school_id is in the JWT payload
        # Set in request.state for easy access
        request.state.school_id = extract_school_id_from_token(request)
        return await call_next(request)

def tenant_filter(query: Query, school_id: str) -> Query:
    """Apply tenant filter to any query."""
    model = query.column_descriptions[0]["entity"]
    if hasattr(model, "school_id"):
        return query.filter(model.school_id == school_id)
    return query

# Service layer pattern:
class StudentService:
    def __init__(self, db: Session, school_id: str):
        self.db = db
        self.school_id = school_id
    
    def get_students(self) -> list[Student]:
        return self.db.query(Student).filter(
            Student.school_id == self.school_id
        ).all()
    
    def get_student(self, student_id: str) -> Student:
        student = self.db.query(Student).filter(
            Student.id == student_id,
            Student.school_id == self.school_id  # ALWAYS filter by tenant
        ).first()
        if not student:
            raise NotFoundError("Student not found")
        return student
```

### 8.3 Database Constraints

```sql
-- Ensure students belong to valid schools
ALTER TABLE students
ADD CONSTRAINT fk_students_school
FOREIGN KEY (school_id) REFERENCES schools(id);

-- Composite unique constraints include school_id where appropriate
ALTER TABLE students
ADD CONSTRAINT uq_students_admission_number
UNIQUE (school_id, admission_number);
```

### 8.4 Testing Tenant Isolation

```python
# tests/test_tenant_isolation.py

async def test_school_a_cannot_access_school_b_student():
    # Create school A with student A1
    # Create school B with student B1
    # Login as management user from school A
    # Attempt to access student B1
    # Assert 404 (not 403, to avoid enumeration)
    ...

async def test_student_cannot_access_another_student():
    # Create two students in same school
    # Login as student A
    # Attempt to access student B's data
    # Assert 403
    ...
```

---

## 9. API Structure

### 9.1 Versioning

All APIs prefixed with `/api/v1/`. Version in URL path for simplicity.

### 9.2 Endpoints

```
Authentication
--------------
POST   /api/v1/auth/login              # Login, get tokens
POST   /api/v1/auth/refresh            # Refresh access token
POST   /api/v1/auth/logout             # Revoke refresh token
POST   /api/v1/auth/logout-all         # Revoke all refresh tokens
POST   /api/v1/auth/change-password    # Change own password

Student Endpoints (Role: student)
---------------------------------
GET    /api/v1/students/me                     # Own profile
GET    /api/v1/students/me/dashboard           # Dashboard data
GET    /api/v1/students/me/attendance          # Own attendance
GET    /api/v1/students/me/attendance/summary  # Attendance stats
GET    /api/v1/students/me/subjects            # Enrolled subjects
GET    /api/v1/students/me/syllabus            # Syllabus for enrolled subjects
GET    /api/v1/students/me/lessons             # Available lessons
GET    /api/v1/students/me/lessons/{id}        # Lesson detail
GET    /api/v1/students/me/results             # Exam results
GET    /api/v1/students/me/results/{exam_id}   # Results for specific exam
GET    /api/v1/students/me/progress            # Learning progress
PUT    /api/v1/students/me/profile             # Update profile (limited fields)

Content (Role: student, teacher)
--------------------------------
GET    /api/v1/content/{id}                    # Get content metadata
GET    /api/v1/content/{id}/url                # Get signed URL for viewing

Teacher Endpoints (Role: teacher)
---------------------------------
GET    /api/v1/teachers/me                         # Own profile
GET    /api/v1/teachers/me/dashboard               # Dashboard
GET    /api/v1/teachers/me/classes                 # Assigned classes
GET    /api/v1/teachers/me/classes/{id}/students   # Students in class
GET    /api/v1/teachers/me/classes/{id}/attendance # Attendance for class
POST   /api/v1/teachers/me/attendance              # Record attendance
PUT    /api/v1/teachers/me/attendance/{id}         # Update attendance record

GET    /api/v1/teachers/me/lessons                 # Own lessons
POST   /api/v1/teachers/me/lessons                 # Create lesson
PUT    /api/v1/teachers/me/lessons/{id}            # Update lesson
DELETE /api/v1/teachers/me/lessons/{id}            # Delete lesson

POST   /api/v1/teachers/me/content/upload-url      # Get presigned upload URL
POST   /api/v1/teachers/me/content                 # Register uploaded content

GET    /api/v1/teachers/me/results                 # Results entry
POST   /api/v1/teachers/me/results                 # Enter results
PUT    /api/v1/teachers/me/results/{id}            # Update result

Management Endpoints (Role: management)
---------------------------------------
# Dashboard
GET    /api/v1/management/dashboard                # Overview stats

# Students
GET    /api/v1/management/students                 # List students (paginated)
POST   /api/v1/management/students                 # Create student
GET    /api/v1/management/students/{id}            # Get student
PUT    /api/v1/management/students/{id}            # Update student
DELETE /api/v1/management/students/{id}            # Deactivate student

# Teachers
GET    /api/v1/management/teachers                 # List teachers
POST   /api/v1/management/teachers                 # Create teacher
GET    /api/v1/management/teachers/{id}            # Get teacher
PUT    /api/v1/management/teachers/{id}            # Update teacher
DELETE /api/v1/management/teachers/{id}            # Deactivate teacher

# Classes & Sections
GET    /api/v1/management/classes                  # List classes
POST   /api/v1/management/classes                  # Create class
GET    /api/v1/management/sections                 # List sections
POST   /api/v1/management/sections                 # Create section
PUT    /api/v1/management/sections/{id}            # Update section

# Subjects
GET    /api/v1/management/subjects                 # List subjects
POST   /api/v1/management/subjects                 # Create subject
PUT    /api/v1/management/subjects/{id}            # Update subject

# Attendance
GET    /api/v1/management/attendance               # View attendance (filters)
GET    /api/v1/management/attendance/report        # Attendance reports

# Results
GET    /api/v1/management/results                  # View results
GET    /api/v1/management/results/report           # Results reports

# Fees (MANAGEMENT ONLY)
GET    /api/v1/management/fees/dashboard           # Fee collection summary
GET    /api/v1/management/fees/students            # Students with fee info
GET    /api/v1/management/fees/students/{id}       # Student fee detail
POST   /api/v1/management/fees/payments            # Record payment
GET    /api/v1/management/fees/payments            # Payment history
GET    /api/v1/management/fees/outstanding         # Outstanding fees report
GET    /api/v1/management/fees/daily-collection    # Daily collection report

# Analytics
GET    /api/v1/management/analytics/overview       # Learning analytics overview
GET    /api/v1/management/analytics/engagement     # Student engagement
GET    /api/v1/management/analytics/content        # Content usage

# School Settings
GET    /api/v1/management/settings                 # School settings
PUT    /api/v1/management/settings                 # Update settings
```

### 9.3 Request/Response Examples

**Login:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "student@school.edu",
  "password": "securepassword123"
}

Response 200:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "550e8400-e29b-41d4-a716-446655440000",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Student Dashboard:**
```http
GET /api/v1/students/me/dashboard
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

Response 200:
{
  "student": {
    "id": "uuid",
    "first_name": "Rahul",
    "last_name": "Sharma",
    "class": "8",
    "section": "A",
    "roll_number": "15"
  },
  "attendance": {
    "total_days": 120,
    "present": 115,
    "absent": 5,
    "percentage": 95.8
  },
  "recent_results": [...],
  "continue_learning": [...],
  "announcements": [...]
}
```

**Record Fee Payment:**
```http
POST /api/v1/management/fees/payments
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "student_id": "student-uuid",
  "amount": 15000.00,
  "payment_date": "2026-09-15",
  "payment_method": "upi",
  "reference_number": "UPI123456789",
  "notes": "Term 2 tuition fee"
}

Response 201:
{
  "id": "payment-uuid",
  "receipt_number": "SJPS-2026-001234",
  "student_id": "student-uuid",
  "amount": 15000.00,
  "payment_date": "2026-09-15",
  "payment_method": "upi",
  "reference_number": "UPI123456789",
  "recorded_by": "admin-user-uuid",
  "created_at": "2026-09-15T10:30:00Z"
}
```

### 9.4 Error Responses

```json
{
  "detail": "Student not found",
  "error_code": "NOT_FOUND",
  "status_code": 404
}

{
  "detail": "Insufficient permissions",
  "error_code": "FORBIDDEN",
  "status_code": 403
}

{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error.email"
    }
  ],
  "error_code": "VALIDATION_ERROR",
  "status_code": 422
}
```

---

## 10. AWS Deployment Architecture

### 10.1 Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   Route 53      │
                                    │  (DNS)          │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
           ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
           │  CloudFront   │       │  CloudFront   │       │  CloudFront   │
           │  (API)        │       │  (Web Apps)   │       │  (Media/CDN)  │
           └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                   │                       │                       │
                   ▼                       ▼                       │
           ┌───────────────┐       ┌───────────────┐               │
           │    AWS WAF    │       │     S3        │               │
           │               │       │  (Static Web) │               │
           └───────┬───────┘       └───────────────┘               │
                   │                                               │
                   ▼                                               ▼
           ┌───────────────┐                               ┌───────────────┐
           │      ALB      │                               │     S3        │
           │               │                               │  (Media)      │
           └───────┬───────┘                               └───────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
     ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Fargate │  │ Fargate │  │ Fargate │     (Auto-scaling)
│ Task 1  │  │ Task 2  │  │ Task N  │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┼────────────┘
                  │
                  ▼
           ┌───────────────┐       ┌───────────────┐
           │  RDS          │       │  Secrets      │
           │  PostgreSQL   │       │  Manager      │
           │  (Multi-AZ)   │       └───────────────┘
           └───────────────┘
                  │
                  ▼
           ┌───────────────┐
           │  CloudWatch   │
           │  Logs/Metrics │
           └───────────────┘
```

### 10.2 Components

| Component | Service | Configuration |
|-----------|---------|---------------|
| DNS | Route 53 | Hosted zone for domain |
| CDN | CloudFront | API caching, static assets, media delivery |
| WAF | AWS WAF | Rate limiting, SQL injection, XSS protection |
| Load Balancer | ALB | HTTPS termination, health checks |
| Compute | ECS Fargate | 2 vCPU, 4GB RAM per task (start) |
| Database | RDS PostgreSQL | db.t3.medium (start), Multi-AZ for prod |
| Storage | S3 | Videos, documents, static web assets |
| Secrets | Secrets Manager | DB credentials, JWT secret, API keys |
| Monitoring | CloudWatch | Logs, metrics, alarms |
| IAM | IAM Roles | Least-privilege for each service |

### 10.3 Environments

| Environment | Purpose | Cost Estimate |
|-------------|---------|---------------|
| Development | Local development | Free (Docker Compose) |
| Staging | Testing, QA | ~$100/month |
| Production | Live pilot | ~$300-500/month |

### 10.4 Cost Optimization for V1

- **Fargate Spot** for staging (70% cheaper)
- **RDS db.t3.micro** for staging
- **S3 Intelligent-Tiering** for media
- **Reserved instances** once stable (save 30-40%)
- **CloudFront caching** to reduce origin requests

---

## 11. Development Roadmap

### Phase 1: Foundation (Weeks 1-3)

**Goal:** Student can login via Flutter app and see dashboard data from PostgreSQL.

```
Week 1:
├── Project setup (repos, CI, Docker)
├── Database schema (core tables)
├── FastAPI scaffolding
├── Auth module (login, JWT, refresh)
└── User/Student models

Week 2:
├── Student APIs (me, dashboard, attendance)
├── Flutter app scaffolding
├── Login screen
├── API integration
└── Secure token storage

Week 3:
├── Dashboard screen
├── Attendance screen
├── Profile screen
├── Integration tests
└── Security review
```

**Deliverable:** Working student login + dashboard on Android emulator.

### Phase 2: Academic Core (Weeks 4-6)

**Goal:** Students can view subjects, syllabus, lessons; Teachers can record attendance.

```
Week 4:
├── Subjects, Classes, Sections models
├── Student enrollment
├── Syllabus module (API + Flutter)
└── Subjects screen

Week 5:
├── Lessons module
├── Content storage (S3 integration)
├── Video playback
└── Lesson screen

Week 6:
├── Teacher web portal scaffolding
├── Teacher auth
├── Attendance recording
└── Teacher dashboard
```

**Deliverable:** Students view lessons; Teachers record attendance via web.

### Phase 3: Results & Analytics (Weeks 7-9)

**Goal:** Teachers enter results; Students view results; Basic analytics.

```
Week 7:
├── Exams module
├── Results entry (teacher)
├── Results display (student)
└── Results API

Week 8:
├── Learning events tracking
├── Basic analytics queries
├── Analytics APIs
└── Student progress view

Week 9:
├── Management portal scaffolding
├── Management auth
├── Student/Teacher CRUD
└── Class management
```

**Deliverable:** Teachers enter marks; Students see results; Management dashboard works.

### Phase 4: Fees & Polish (Weeks 10-12)

**Goal:** Fee management complete; Production deployment; Pilot launch.

```
Week 10:
├── Fee structures
├── Student fee accounts
├── Payment recording
├── Fee dashboard

Week 11:
├── AWS infrastructure (CDK)
├── Staging deployment
├── Load testing
├── Security audit

Week 12:
├── Production deployment
├── Monitoring setup
├── Documentation
├── Pilot launch (100-300 students)
```

**Deliverable:** Production system live with St Joseph's pilot.

### Post-Pilot (Weeks 13+)

- Bug fixes from pilot feedback
- Performance optimization
- Scale testing toward 7,000 students
- Teacher mobile app (if needed)
- Advanced analytics
- AI features (V2)

---

## 12. Security Considerations

### 12.1 Data Protection

- All data encrypted at rest (RDS, S3)
- All data encrypted in transit (HTTPS/TLS 1.3)
- Sensitive fields (phone, address) encrypted at application level if required
- PII access logged to audit table

### 12.2 Authentication Security

- Passwords hashed with Argon2id
- JWT access tokens short-lived (15 min)
- Refresh tokens stored hashed, revocable
- Rate limiting on auth endpoints
- Account lockout after failed attempts

### 12.3 Authorization Security

- Backend enforces all permissions
- Every query filters by school_id
- Role checks on every protected endpoint
- No client-side security assumptions

### 12.4 API Security

- Input validation via Pydantic
- SQL injection protection via ORM
- XSS protection (React escapes by default)
- CORS configured for known origins only
- Rate limiting via WAF
- Request size limits

### 12.5 Infrastructure Security

- VPC with private subnets for RDS
- Security groups restrict access
- IAM roles with least privilege
- Secrets in Secrets Manager (not env vars in code)
- No public database access

### 12.6 Operational Security

- Audit logging for sensitive operations
- CloudWatch alarms for anomalies
- Regular dependency updates
- No secrets in Git (enforced via pre-commit hooks)

---

## 13. Open Questions

Before implementation, please confirm or clarify:

1. **Repository location:** Same GitHub account (`balasukumarTR`)? New repo name (`school-saas-platform`)?

2. **Domain name:** What domain will the platform use? (Needed for SSL certs, CORS)

3. **School branding:** Should each school's branding (logo, colors) be configurable in V1, or is St Joseph's hardcoded acceptable initially?

4. **SMS/Email:** Will we need SMS for OTP or notifications in V1? Which provider?

5. **Fee payment integration:** Record-only in V1, or integrate with payment gateway (Razorpay, etc.)?

6. **Offline support:** Does the Flutter app need offline mode for areas with poor connectivity?

7. **Teacher mobile app:** Is web-only acceptable for teachers in V1, or do they need a mobile app too?

8. **Academic calendar:** Indian school year (April-March) or flexible per school?

---

## Approval

Please review this architecture proposal and confirm:

- [ ] Overall architecture approved
- [ ] Technology stack approved
- [ ] Database design approved
- [ ] API structure approved
- [ ] Development roadmap approved

Once approved, I will begin **Phase 1: Foundation** — setting up the project structure, database schema, and authentication system.

---

*Document version: 1.0*  
*Last updated: 2026-09-15*
