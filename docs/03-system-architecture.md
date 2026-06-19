# PREPOS AI

# Founder Master Blueprint

# Part 3 — Technical Architecture Blueprint

Version: 1.0

Status: Architecture Draft

---

# 1. Architecture Principles

The platform must be designed as:

* AI Native
* SaaS First
* Multi-Tenant
* Enterprise Ready
* Cloud Native
* Event Driven
* Observable
* Extensible

The system should support:

* Individual Students
* Coaching Institutes
* Enterprise Coaching Networks

without requiring architecture rewrites.

---

# 2. Architectural Goals

Primary Goals

* Scale to 100,000+ students
* Support thousands of concurrent assessments
* Support AI workloads
* Support coaching institutions
* Support future mobile apps

Non-Goals

* Microservices on Day 1
* Kubernetes on Day 1
* Premature optimization

---

# 3. High-Level Architecture

```
                Frontend Layer
                       |
                API Gateway Layer
                       |
             -----------------------
             |                     |
      Core Application      AI Platform
             |                     |
             -----------------------
                       |
                 Data Layer
                       |
             -----------------------
             |          |          |
         Postgres     Redis     Vector DB
```

---

# 4. Technology Stack

Frontend

* Next.js 15
* React 19
* TypeScript
* Tailwind CSS
* shadcn/ui
* React Query
* Zustand
* React Hook Form
* Zod

Backend

* Python 3.13+
* FastAPI
* SQLAlchemy 2
* Pydantic v2
* Alembic

Background Processing

* Celery
* Redis

Database

* PostgreSQL 17

Vector Search

* pgvector

Caching

* Redis

AI Framework

* LangGraph
* LangChain
* OpenAI SDK

Storage

* AWS S3

Infrastructure

* Docker
* Docker Compose
* AWS

CI/CD

* GitHub Actions

Monitoring

* OpenTelemetry
* Grafana
* Prometheus
* Sentry

---

# 5. SaaS Architecture

The system is multi-tenant.

Tenant Types

1. Individual User

Example:

Student purchases subscription.

---

2. Coaching Institute

Example:

Institute manages:

* Students
* Faculties
* Batches

---

3. Enterprise

Multiple branches.

Multiple faculties.

Thousands of students.

---

# Multi-Tenant Strategy

Shared Database

Shared Schema

Every table contains:

tenant_id

Example:

users
students
assessments
learning_graph
plans

All tenant scoped.

---

# Why Shared Schema

Pros

* Simple
* Cheap
* Easy maintenance

Future

Can migrate enterprise tenants to isolated databases.

---

# 6. Domain Driven Design

Modules

Auth

Student

Faculty

Institute

Syllabus

LearningGraph

Revision

Assessment

Mentor

PYQ

Knowledge

CurrentAffairs

Analytics

Billing

Notifications

AI

Each module owns:

* Models
* Services
* Repositories
* APIs

---

# 7. Backend Folder Structure

backend/

src/

api/

application/

domain/

infrastructure/

ai/

tasks/

tests/

---

# Domain Layer

domain/

auth/

student/

faculty/

institute/

syllabus/

learning_graph/

revision/

mentor/

assessment/

pyq/

analytics/

---

# Application Layer

application/

use_cases/

services/

dto/

validators/

---

# Infrastructure Layer

database/

repositories/

external/

cache/

storage/

messaging/

---

# AI Layer

ai/

agents/

graphs/

tools/

prompts/

memory/

evaluation/

---

# 8. Frontend Architecture

frontend/

src/

app/

components/

features/

hooks/

stores/

lib/

types/

---

# Feature-Based Structure

features/

auth/

dashboard/

learning-graph/

mentor/

revision/

assessment/

analytics/

institute/

---

# State Management

React Query

Server State

Examples

* assessments
* plans
* revisions

---

Zustand

Client State

Examples

* active session
* theme
* UI state

---

# 9. Authentication Architecture

Authentication

JWT Access Token

Refresh Token

RBAC

Roles

Student

Faculty

Institute Admin

Super Admin

---

# Security

Access Token

15 Minutes

Refresh Token

7 Days

Stored in HttpOnly Cookies

---

# 10. Event Driven Architecture

Many actions trigger events.

Examples

TopicCompleted

AssessmentFinished

RevisionCompleted

AnswerEvaluated

StudentRegistered

---

Events published to Redis.

Workers process asynchronously.

---

# Example

Assessment Finished

Triggers

Update Learning Graph

Update Twin

Generate Analytics

Generate Mentor Insights

---

# 11. AI Architecture

The platform uses a hybrid architecture.

Deterministic Engines

*

AI Agents

---

Deterministic

Mastery Calculation

Revision Scheduling

Scoring

Analytics

Importance Calculation

---

AI

Planning

Recommendations

Evaluation

Explanations

Mentoring

---

# Rule

Never use LLMs when algorithms are sufficient.

---

# 12. Agent Architecture

Mentor Agent

Revision Agent

Assessment Agent

Knowledge Agent

Current Affairs Agent

Faculty Agent

Institute Analyst Agent

---

Supervisor Agent

Routes requests.

Coordinates workflows.

---

# Example

Student asks

"What should I study today?"

Supervisor

↓

Mentor Agent

↓

Learning Graph

↓

Revision Engine

↓

PYQ Engine

↓

Daily Plan

---

# 13. AI Memory System

Three Layers

Short Term Memory

Conversation

---

Long Term Memory

Student Preferences

---

Preparation Twin

Learning History

Mastery

Retention

Assessment Data

---

# 14. Assessment Architecture

Assessment Types

MCQ

Mains

Essay

Interview

---

Assessment Pipeline

Create

Attempt

Evaluate

Analyze

Update Twin

Update Learning Graph

Generate Mentor Feedback

---

# 15. Knowledge Architecture

Knowledge Sources

NCERT

Standard Books

Current Affairs

Government Reports

PYQs

Institute Material

---

Pipeline

Upload

Chunk

Embed

Store

Retrieve

Answer

---

# Vector Architecture

pgvector

Single source of truth

No Chroma

No Pinecone initially

---

# 16. Notification Architecture

Channels

In-App

Email

Push

WhatsApp (Future)

---

Examples

Revision Due

Plan Generated

Assessment Ready

Performance Alert

---

# 17. Analytics Architecture

Student Analytics

Mastery

Retention

Revision

Performance

---

Faculty Analytics

Batch Health

Weak Topics

Strong Topics

---

Institute Analytics

Enrollment

Retention

Performance

Revenue

---

# 18. Caching Strategy

Redis

Used For

Sessions

Rate Limits

Mentor Plans

Analytics

Frequently Used Queries

---

# 19. Search Architecture

Hybrid Search

Vector Search

*

Keyword Search

Used For

Knowledge Retrieval

PYQ Search

Current Affairs Search

---

# 20. File Storage Architecture

AWS S3

Stores

PDFs

Notes

Reports

Images

Answer Sheets

Generated Documents

---

# 21. DevOps Architecture

Development

Docker Compose

---

Staging

AWS EC2

Docker

---

Production

AWS ECS Fargate

RDS

ElastiCache

S3

CloudFront

---

# 22. CI/CD

GitHub Actions

Pipeline

Lint

Test

Build

Security Scan

Deploy

Smoke Test

---

# 23. Monitoring

Metrics

Prometheus

---

Dashboards

Grafana

---

Errors

Sentry

---

Tracing

OpenTelemetry

---

# 24. Security Architecture

Encryption

TLS Everywhere

---

Database

Encrypted at Rest

---

Secrets

AWS Secrets Manager

---

Protection

Rate Limiting

RBAC

Audit Logs

Prompt Injection Protection

Tenant Isolation

---

# 25. Scalability Roadmap

Phase 1

10,000 Students

Single Region

---

Phase 2

100,000 Students

Horizontal Scaling

---

Phase 3

1M+ Students

Microservices

Multi Region

---

# 26. Architecture Rulebook

Rule 1

Business Logic never inside API routes.

---

Rule 2

Repositories never return ORM models to API.

---

Rule 3

Agents cannot directly access database.

Must go through services.

---

Rule 4

Every AI decision must be explainable.

---

Rule 5

Learning Graph is source of truth.

---

Rule 6

Preparation Twin is the intelligence layer.

---

Rule 7

AI assists decisions.

AI never becomes the source of truth.

---

END OF PART 2
