PREPOS AI
Founder Master Blueprint
Part 6 — Backend Architecture, Services, APIs, Events & Implementation Blueprint

Version: 1.0

Status: Engineering Execution Blueprint

1. Backend Philosophy

The backend is responsible for:

Truth
Consistency
Security
Scalability
Observability

The AI layer sits on top.

The backend remains the source of truth.

2. Architecture Style

Chosen:

Modular Monolith

Not:

Microservices
Why?

For first 2 years:

Benefits:

Faster development
Easier debugging
Lower cloud cost
Simpler deployments
Easier Cursor development

Future:

Can extract modules into services.

3. High Level Architecture
Client

 ↓

API Gateway

 ↓

Application Services

 ↓

Domain Layer

 ↓

Repositories

 ↓

PostgreSQL

Redis

S3

pgvector

OpenAI
4. Backend Folder Structure
backend/

src/

api/

application/

domain/

infrastructure/

ai/

events/

tasks/

tests/
5. API Layer

Responsibilities:

Request Validation
Authentication
Authorization
Response Serialization

Must NOT contain:

Business Logic
Structure
api/

auth/

students/

institutes/

assessments/

mentor/

revision/

learning_graph/

analytics/
6. Application Layer

Contains:

Use Cases
Services
DTOs
Validators

Examples

GenerateDailyPlan

CompleteRevision

SubmitAssessment

EvaluateMainsAnswer
7. Domain Layer

Contains:

Entities

Value Objects

Rules

Domain Events

Examples

Student

Assessment

Revision

LearningGraph
8. Infrastructure Layer

Contains:

Postgres

Redis

S3

pgvector

External APIs
9. Core Services

The platform revolves around these services.

Auth Service

Responsibilities:

Register

Login

Refresh

RBAC
Student Service

Responsibilities:

Profile

Goals

Preparation Preferences
Learning Graph Service

Responsibilities:

Update Mastery

Update Retention

Update Confidence

This service is the heart of the system.

Revision Service

Responsibilities:

Generate Revisions

Schedule Revisions

Track Completion
Assessment Service

Responsibilities:

Create

Submit

Evaluate

Analyze
Mentor Service

Responsibilities:

Generate Daily Plans

Generate Weekly Plans

Generate Monthly Plans
Knowledge Service

Responsibilities:

RAG

Search

Notes
Analytics Service

Responsibilities:

Student Analytics

Faculty Analytics

Institute Analytics
10. PostgreSQL Design

Postgres remains:

Source Of Truth
Core Tables
tenants
id UUID PK

name

slug

tenant_type

plan

status

created_at
users
id UUID PK

tenant_id

email

password_hash

role

status

created_at
students
id UUID

user_id

target_exam_id

target_year

daily_hours

experience_level
exams
id UUID

name

code

exam_type
syllabus_nodes
id UUID

exam_id

parent_id

name

level

description
student_concept_progress

MOST IMPORTANT TABLE

id UUID

student_id

concept_id

mastery_score

retention_score

confidence_score

importance_score

updated_at
preparation_twins
id UUID

student_id

knowledge_profile JSONB

behavior_profile JSONB

assessment_profile JSONB

prediction_profile JSONB
mentor_plans
id UUID

student_id

date

plan_json

reasoning_json
revisions
id UUID

student_id

concept_id

scheduled_date

completed_date

status
assessments
id UUID

student_id

type

subject

status

created_at
assessment_attempts
id UUID

assessment_id

student_id

score

accuracy

time_taken
current_affairs
id UUID

title

summary

importance_score

published_date
pyq_questions
id UUID

exam_id

year

question_text

difficulty
pyq_mappings
question_id

concept_id

weight
11. Vector Database Design

Chosen:

PostgreSQL + pgvector

Table

knowledge_chunks

id UUID

source_id

content

embedding vector(3072)

metadata JSONB

Sources

Books

Notes

Current Affairs

PYQs

Government Reports
12. Event Architecture

Every significant action generates events.

Example

AssessmentSubmitted

Triggers

Update Learning Graph

Update Twin

Generate Analytics

Generate Mentor Insights
Event Examples
StudentRegistered

TopicCompleted

RevisionCompleted

AssessmentCompleted

AnswerEvaluated

PlanGenerated
13. Redis Usage

Redis is critical.

Used for:

Caching

Queues

Rate Limiting

Sessions

Pub/Sub
14. Celery Architecture

Async jobs.

Queues

assessment

revision

knowledge

analytics

notifications
Example

User submits answer.

Flow

Submit Answer

↓

Create Job

↓

Celery Worker

↓

AI Evaluation

↓

Store Results

↓

Notify User
15. RAG Pipeline

Upload

↓

Extract

↓

Chunk

↓

Embed

↓

Store

↓

Retrieve

↓

Generate

Chunk Size

500-800 tokens

Overlap

100 tokens
16. Assessment Pipeline

MCQ

↓

Score

↓

Analyze

↓

Update Graph

↓

Update Twin

Mains

↓

AI Evaluation

↓

Human Override Optional

↓

Update Graph

↓

Update Twin

17. Learning Graph Engine

This is a service.

Not an AI agent.

Responsibilities

Calculate Mastery

Calculate Retention

Calculate Confidence

Example API

POST /internal/learning-graph/update
18. Retention Engine

Runs nightly.

Calculates:

Retention Decay

Revision Needs

Revision Priority

Creates:

Revision Tasks
19. Mentor Plan Engine

Runs:

Daily
Weekly
Monthly

Input

Learning Graph

Preparation Twin

PYQ Intelligence

Output

Personalized Plan

Stored in:

mentor_plans
20. Notification Service

Channels

Email

Push

In-App

Examples

Revision Due

Plan Ready

Assessment Completed
21. Search Service

Hybrid Search

Vector

+

Keyword

Tools

Postgres Full Text Search

pgvector
22. API Design

Versioned APIs.

Base

/api/v1

Examples

Auth

POST /auth/register

POST /auth/login

POST /auth/refresh

Student

GET /students/me

PATCH /students/me

Learning Graph

GET /learning-graph

GET /learning-graph/concepts

Mentor

GET /mentor/today

GET /mentor/week

GET /mentor/month

Revision

GET /revisions/today

POST /revisions/{id}/complete

Assessments

POST /assessments

GET /assessments/{id}

POST /assessments/{id}/submit

Knowledge

POST /knowledge/ask

Current Affairs

GET /current-affairs

Analytics

GET /analytics/dashboard
23. WebSocket Architecture

Used for:

AI Streaming

Notifications

Assessment Updates

Endpoint

/ws

Events

{
  "type":"token"
}
{
  "type":"plan_generated"
}
{
  "type":"assessment_complete"
}
24. Security Architecture

JWT

RBAC

Rate Limits

Audit Logs

Prompt Protection

All writes logged.

25. Audit Logging

Track:

Student Actions

Faculty Actions

Admin Actions

AI Decisions
26. Observability

Every request has:

request_id

tenant_id

user_id

Track

Latency

Cost

Errors

AI Usage
27. Testing Strategy

Unit Tests

Integration Tests

E2E Tests

AI Evaluation Tests

Coverage Goal

80%
28. Development Roadmap

Phase 1

Foundation

4 weeks

Deliver

Auth

Students

Exams

Syllabus

Learning Graph

Phase 2

Core Intelligence

4 weeks

Deliver

Revision Engine

Preparation Twin

Mentor Engine

Phase 3

Assessment

4 weeks

Deliver

MCQ

Mains

AI Evaluation

Phase 4

Knowledge

4 weeks

Deliver

RAG

Current Affairs

PYQ Intelligence

Phase 5

Institutes

4 weeks

Deliver

Faculty

Institute Dashboards

Analytics

Phase 6

Production

4 weeks

Deliver

Monitoring

Security

CI/CD

Scaling
29. Architecture Decisions
Why FastAPI?
Python ecosystem
AI friendly
Excellent performance
Why PostgreSQL?
Reliability
JSONB
pgvector
Why LangGraph?
Agent orchestration
Stateful workflows
Why Redis?
Cache
Queue
Pub/Sub
Why Modular Monolith?
Faster execution
Easier maintenance
30. Cursor Implementation Rulebook

When Cursor generates code:

Rule 1

No business logic in routes.

Rule 2

All modules independent.

Rule 3

Services own business logic.

Rule 4

Learning Graph service never depends on AI.

Rule 5

Preparation Twin updates through events.

Rule 6

AI agents use tools.

Never direct DB access.

Rule 7

Every feature must be observable.

Rule 8

Everything must be tenant-aware.

End of Part 6