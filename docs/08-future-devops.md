PREPOS AI
Part 8 — Enterprise AWS, DevOps, Security, Scalability & Operations Blueprint

Version: 1.0

Status: Production Architecture

1. Infrastructure Philosophy
Wrong Approach

Build for:

100,000 users

on Day 1.

Result:

Complex
Expensive
Slow development
Right Approach

Build for:

100 users

while keeping architecture capable of growing to:

100,000+
2. AWS Services Selection
Layer	Service
Frontend	Next.js
Backend	FastAPI
Containers	Docker
Container Platform	ECS Fargate
Database	PostgreSQL RDS
Cache	Redis ElastiCache
File Storage	S3
CDN	CloudFront
Authentication	Internal JWT
Secrets	AWS Secrets Manager
Monitoring	CloudWatch
Error Tracking	Sentry
Queue	Redis + Celery
AI Models	OpenAI + Anthropic
Search	PostgreSQL + pgvector
3. Architecture Evolution
Stage 1

100 Users

CloudFront
    ↓
ALB
    ↓
ECS Service
    ↓
RDS PostgreSQL

Redis

S3

Cost Efficient.

Stage 2

1,000 Users

Multiple ECS Tasks

Read Replicas

Redis HA
Stage 3

10,000 Users

Dedicated Workers

Dedicated AI Queue

Separate Search Service
Stage 4

100,000 Users

Microservices

Only if necessary.

4. AWS Account Structure

Use:

1 AWS Organization

Accounts

Management

Development

Staging

Production

Never deploy production in the development account.

5. VPC Architecture

Production VPC

10.0.0.0/16

Subnets

Public
ALB

NAT Gateway
Private App
ECS Tasks
Private Data
RDS

Redis

No database should ever be public.

6. Networking Flow
User

↓

CloudFront

↓

WAF

↓

ALB

↓

ECS

↓

RDS
7. ECS Decision

Choose:

ECS Fargate

Not:

EKS

Initially.

Why?

Simpler
Lower maintenance
Lower operational burden
Faster deployment
8. Container Strategy

Containers

frontend
Next.js
api
FastAPI
worker
Celery
beat
Scheduler
9. RDS PostgreSQL

Start

db.t4g.medium

Storage

100 GB

Features

Automated Backups

Multi-AZ

Production only.

10. PostgreSQL Strategy

Database remains:

Single Source Of Truth

Use:

JSONB
pgvector
Full Text Search

Avoid introducing:

Elasticsearch
Neo4j
MongoDB

early.

11. Redis Architecture

Use:

ElastiCache Redis

Purposes

Caching

Queues

Sessions

Pub/Sub

Rate Limiting
12. S3 Strategy

Buckets

Documents
prepos-documents
User Uploads
prepos-user-content
Backups
prepos-backups

Folder Convention

tenant_id/project_id/file
13. CloudFront

All traffic enters through CloudFront.

Benefits:

CDN
DDoS mitigation
SSL
Caching
14. WAF Rules

Protect against:

SQL Injection
XSS
Bot Abuse
Credential Stuffing

Use AWS Managed Rules.

15. Secrets Management

Never store:

OPENAI_API_KEY

in:

Code
Docker Images
GitHub

Store in:

AWS Secrets Manager
16. Environment Variables

Inject at runtime.

Example:

DATABASE_URL

REDIS_URL

OPENAI_API_KEY

JWT_SECRET
17. CI/CD Architecture

Chosen:

GitHub Actions

Workflow

Push

↓

Tests

↓

Build Docker

↓

Push ECR

↓

Deploy ECS
18. Deployment Environments
Dev

Auto deploy

Staging

Auto deploy

Production

Manual approval

Always.

19. Monitoring

Required Day 1.

Use:

CloudWatch

Infrastructure

Sentry

Application

OpenTelemetry

Tracing

20. Metrics To Track
API
Latency

Error Rate

Requests
AI
Tokens

Cost

Success Rate
Product
DAU

Retention

Completion Rate
21. Logging Standard

Every log includes:

{
  "request_id":"",
  "tenant_id":"",
  "user_id":"",
  "service":""
}
22. AI Cost Monitoring

Track per:

User

Institute

Feature

Agent

Store:

Prompt Tokens

Completion Tokens

Cost
23. AI Model Strategy

Use:

GPT Models

Complex reasoning

Anthropic Models

Long-context evaluation

Small Models

Classification

Routing

Tagging

Don't use expensive models for everything.

24. Scaling AI Costs

Pattern:

Simple Task
→ Small Model

Medium Task
→ GPT

Complex Task
→ Claude

Expected cost reduction:

60–80%
25. Queue Architecture

Celery Queues

revision

Revision calculations

mentor

Plan generation

assessment

Evaluation

ingestion

RAG indexing

analytics

Insights

26. Disaster Recovery

Backups

PostgreSQL

Daily

S3

Versioning

Redis

Snapshots

Recovery Target

RPO < 24h

RTO < 4h
27. Security Controls

Authentication

JWT

Refresh Tokens

Authorization

RBAC

Tenant Isolation

Encryption

TLS Everywhere

AES At Rest

28. Multi-Tenant Security

Every table contains:

tenant_id

Every query filtered by:

tenant_id

Mandatory.

29. AI Security

Threats

Prompt Injection
Data Leakage
Jailbreaks
Toxic Outputs

Protection

System Prompts

Guardrails

Output Validation

Tenant Boundaries
30. Compliance Roadmap

Year 1

Basic Security

Year 2

SOC2 Type 1

Year 3

SOC2 Type 2
31. Cost Estimates
Development Stage

0–100 users

Service	Monthly
ECS	$20–40
RDS	$20–30
Redis	$15–20
S3	$5
CloudFront	$5
Monitoring	$10
AI Usage	$20–100
Total	~$100–200
Early Growth

1,000 users

Service	Monthly
Infra	$300–600
AI	$500–2000
Total	~$1000–2500
Growth Stage

10,000 users

Service	Monthly
Infra	$2000–5000
AI	$5000–15000
Total	~$7000–20000
32. Revenue Targets
Individual Aspirants

₹299–999/month

Premium

₹1499–2999/month

Institutes

₹25,000–2,00,000/month

This is where the real money is.

33. Moat Strategy

Most competitors build:

Chatbot

Your moat:

Learning Graph

Revision Engine

Preparation Twin

Assessment Intelligence

Institution Analytics

These improve with data.

34. Scaling Path
100 users

↓

1000 users

↓

10000 users

↓

100000 users

No major rewrites required.

35. CTO Final Recommendation

If I were founding this company today:

Phase 1 (First 4 Months)

Build only:

Learning Graph
Revision Engine
Mentor
MCQ Assessment

Skip advanced agents.

Phase 2 (Months 5–8)

Add:

Knowledge Hub
RAG
Current Affairs Intelligence
Phase 3 (Months 9–12)

Add:

Mains Evaluation
Faculty Portal
Institution Analytics
Phase 4

Add:

Marketplace
Interview Coaching
Institution Intelligence
Final Verdict

Among all ideas discussed, the strongest long-term product is:

PrepOS

AI Operating System for Competitive Exam Preparation

because it is not merely an AI chatbot.

It becomes a personalized preparation infrastructure layer for:

UPSC
TSPSC
APPSC
State PSCs
SSC
Banking
Railways
CAT
GATE

and later can evolve into a broader education intelligence platform.