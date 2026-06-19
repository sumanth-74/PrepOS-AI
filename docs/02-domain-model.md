PREPOS AI
Founder Master Blueprint
Part 2 — Domain Model, Database Architecture, Learning Graph & Preparation Twin

Version: 1.0

Status: Core Intellectual Property Design

1. Domain Philosophy

Traditional platforms store:

User
Course
Lesson
Test

We store:

User
Knowledge
Retention
Mastery
Revision
Performance
Behavior
Prediction

because the goal is not content delivery.

The goal is:

Preparation Intelligence
2. Core Domain Model

The entire system revolves around:

Tenant
 ├── Student
 ├── Faculty
 ├── Batch
 ├── Exam
 ├── Syllabus
 ├── Learning Graph
 ├── Preparation Twin
 ├── Assessments
 ├── Revision Plans
 ├── Mentor Plans
 └── Analytics
3. Multi-Tenant Entities
Tenant

Represents:

Individual User
Coaching Institute
Enterprise Institute
Fields
id UUID
name
slug
tenant_type
plan
status
created_at
4. User Entities
User
id UUID
tenant_id
email
password_hash
role
status
created_at

Roles:

student
faculty
institute_admin
super_admin
5. Student Entity
Student
id UUID
tenant_id
user_id

target_exam_id

target_attempt_year

study_hours_per_day

experience_level

onboarding_completed

created_at
6. Exam Entity

Examples:

UPSC
APPSC Group 1
TSPSC Group 1
id UUID

name

exam_type

prelims_weight

mains_weight

interview_weight
7. Syllabus Intelligence Model

This is extremely important.

Instead of PDFs:

Store syllabus as graph.

SyllabusNode
id UUID

exam_id

parent_id

name

description

level

node_type

created_at

Example

UPSC
 └── GS2
      └── Polity
           └── Fundamental Rights

Levels:

Subject
Topic
Subtopic
Concept
8. Knowledge Graph

Every concept can be linked.

Example:

Fundamental Rights
        |
        +--- DPSP
        |
        +--- Fundamental Duties

Table

concept_relationships

source_node_id

target_node_id

relationship_type

Relationship Types

prerequisite
related
dependent
frequently_asked_with
9. PYQ Intelligence Model

One of the biggest differentiators.

PYQ Question
id

exam_id

year

paper

question_text

question_type

difficulty

marks
PYQ Mapping

Maps questions to concepts.

pyq_concepts

question_id

concept_id

weight

Example

Question
    |
    +---- Fundamental Rights
    |
    +---- Judiciary
10. Importance Engine

Every concept gets:

Importance Score

Range:

0 - 100

Formula

Importance

=

PYQ Frequency

+
Recent Trend

+
Exam Relevance

+
Faculty Weight

Example

Fundamental Rights

95

Example

Governor Powers

78
11. Learning Graph

This is the platform's heart.

Every student gets:

Student
   |
Learning Graph
   |
Concept Nodes

Each concept contains:

Mastery
Retention
Confidence
Importance
Student Concept Progress
student_concept_progress

student_id

concept_id

mastery_score

retention_score

confidence_score

importance_score

last_updated
12. Mastery Score

Measures understanding.

Range

0-100

Sources

Study Sessions

MCQ Performance

Mains Performance

Revision Results

Formula

40% MCQ

30% Mains

20% Revision

10% Study Activity

Example

Mastery

82

Interpretation

0-40 Weak

40-70 Moderate

70-90 Strong

90-100 Expert
13. Confidence Score

Measures perceived understanding.

Sources

Student Self Assessment

Question Response Speed

Consistency

Example

Mastery = 40

Confidence = 90

System detects:

Overconfidence
14. Retention Score

Most important metric.

Measures:

How much student remembers

Range

0-100

Factors

Time Since Study

Time Since Revision

Assessment Results
Retention Decay

Inspired by:

Hermann Ebbinghaus forgetting curve.

Example

Day 0

Retention = 100

Day 7

Retention = 72

Day 15

Retention = 55

Day 30

Retention = 35

Revisions increase retention.

15. Revision Engine

Purpose:

Fight forgetting

Every day system calculates:

Revision Priority

Formula

Priority

=

Importance

×

Retention Gap

×

Exam Proximity

×

Weakness Score

Output

Top 20 Revision Items
16. Revision Health

Student-level metric.

Formula

Completed Revisions

/

Scheduled Revisions

Range

0-100

Example

Revision Health

92
17. Preparation Twin

This is the moat.

Most competitors store:

Progress

We store:

Preparation Identity
Preparation Twin

Digital representation of:

Knowledge

Behavior

Retention

Writing

Accuracy

Discipline

Consistency
Twin Structure
Preparation Twin

├── Knowledge Profile

├── Revision Profile

├── Assessment Profile

├── Behavior Profile

├── Prediction Profile
18. Knowledge Profile

Contains:

Strong Topics

Weak Topics

Mastery Distribution

Retention Distribution
19. Assessment Profile

Contains:

MCQ Accuracy

Negative Marking Risk

Mains Quality

Essay Quality
20. Behavior Profile

Contains:

Study Consistency

Revision Discipline

Preferred Study Time

Session Duration
21. Prediction Engine

Most advanced feature.

Predict:

Likely Prelims Score

Likely Mains Score

Risk Areas

Success Probability

Example

Predicted Prelims

84 ± 6
22. Daily Planning Engine

Input

Learning Graph

Preparation Twin

PYQ Intelligence

Exam Calendar

Output

Today's Plan

Plan Contains

Study

Revision

MCQs

Mains Writing
23. Assessment Domain

Assessment

Attempt

Question

Evaluation

Feedback

Analytics

Assessment
id

student_id

assessment_type

subject

created_at

Types

MCQ

Mains

Essay

Interview
24. MCQ Analytics

Store:

Accuracy

Speed

Confidence

Guessing Rate
25. Mains Analytics

Store:

Structure

Content

Examples

Flow

Keywords

Generated by AI.

26. Current Affairs Domain

Current Affair

Topic

Source

Category

Mapped Concepts

Importance

Current Affairs automatically link to:

Syllabus Concepts

Example

Climate Summit

↓

Environment

↓

International Agreements
27. Mentor Plan Entity
mentor_plans

student_id

date

study_tasks

revision_tasks

assessment_tasks

generated_reasoning

Reasoning stored.

Why?

Explainability.

28. Institutional Analytics

Institute

↓

Batch

↓

Student

↓

Learning Graph

↓

Analytics

Examples

Top Weak Topics

Top Strong Topics

Revision Compliance

Faculty Effectiveness
29. Database Philosophy

PostgreSQL remains:

Source of Truth

Everything else derives from it.

Stores:

Users

Students

Learning Graph

Preparation Twin

Assessments

Plans

Analytics
30. Competitive Moats

Level 1

Content

Easy to copy.

Level 2

AI Chat

Easy to copy.

Level 3

RAG

Moderately easy to copy.

Level 4

Learning Graph

Hard to copy.

Level 5

Preparation Twin

Very hard to copy.

Level 6

Prediction Engine

Extremely hard to copy.

