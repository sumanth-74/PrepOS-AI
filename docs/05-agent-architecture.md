PREPOS AI
Founder Master Blueprint
Part 5 — AI Architecture & Agent System

Version: 1.0

Status: Strategic Moat Layer

1. AI Philosophy

AI is NOT the product.

AI is an intelligence layer that enhances:

Learning
Planning
Revision
Evaluation
Prediction

The source of truth is:

Learning Graph
+
Preparation Twin
+
Assessment History

Not the LLM.

2. AI System Layers
┌──────────────────────────────┐
│       User Experience        │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│       Supervisor Agent       │
└──────────────┬───────────────┘
               │
 ┌─────────────┼─────────────┐
 │             │             │
 ▼             ▼             ▼

Mentor     Revision      Assessment
Agent       Agent          Agent

 ▼             ▼             ▼

Knowledge  Current      Institute
Agent      Affairs      Agent

             ▼
       Faculty Agent

               ▼
         Tool Layer

               ▼
Learning Graph
Preparation Twin
Assessments
Knowledge Base
3. Why Multi-Agent?

Single-agent systems become:

expensive
inconsistent
difficult to maintain

Multi-agent systems allow:

specialization
lower costs
explainability
modular growth
4. Supervisor Agent

The brain.

Responsibilities:

Understand user intent
Route tasks
Combine outputs
Resolve conflicts
Maintain context

Example

Student asks:

What should I study today?

Supervisor does NOT answer.

It routes to:

Mentor Agent

Student asks:

Evaluate my answer.

Routes to:

Assessment Agent

Student asks:

Explain federalism.

Routes to:

Knowledge Agent
5. Mentor Agent

Most important agent.

Acts like:

Senior UPSC Mentor

Responsibilities:

Daily plans
Weekly plans
Monthly plans
Prioritization
Guidance

Inputs:

Learning Graph

Preparation Twin

Exam Calendar

PYQ Intelligence

Revision Engine

Outputs:

Study Tasks

Revision Tasks

Assessment Tasks

Example Output

Today:

1. Revise Fundamental Rights
2. Read Governor Powers
3. Solve 30 MCQs
4. Write 1 GS2 answer
6. Revision Agent

Purpose:

Fight forgetting

Responsibilities:

Determine what to revise
Determine revision order
Determine revision intensity

Inputs:

Retention Score

Importance Score

Exam Proximity

Weakness Score

Outputs:

Revision Plan
7. Assessment Agent

Acts as:

UPSC Evaluator

Responsibilities:

Evaluate MCQs
Evaluate Mains Answers
Evaluate Essays
Generate feedback

Output Example

Score: 6/10

Strengths:

Good structure

Weaknesses:

Lack of examples

Missing constitutional references
8. Knowledge Agent

Purpose:

Personal Tutor

Powered by:

RAG
Knowledge Base
Current Affairs

Responsibilities:

Explain concepts
Generate notes
Create summaries
Answer doubts

Example

Explain DPSP.

Produces:

Explanation
Examples
PYQ references
Mains relevance
9. Current Affairs Agent

Purpose:

Connect current affairs to syllabus.

Input

Current Event

Output

Summary

Importance

Related Concepts

Possible Questions

Example

RBI Monetary Policy

Maps to:

Economy

Inflation

Monetary Policy
10. Faculty Agent

For coaching institutes.

Responsibilities:

Generate tests
Generate assignments
Create notes
Generate discussions

Example

Create GS2 test on Parliament.

Outputs:

MCQs

Mains Questions

Model Answers
11. Institute Analyst Agent

Purpose:

Institute Intelligence.

Inputs:

Students

Batches

Assessments

Learning Graphs

Outputs:

Weak Topics

Batch Health

Risk Students

Faculty Insights
12. Interview Agent (V2)

Acts as:

UPSC Interview Board

Features:

Mock Interviews
Follow-up Questions
Personality Feedback

Future:

Voice Enabled

13. AI Memory Architecture

Three levels.

Level 1

Conversation Memory

Short term.

Stores:

Recent Chats

Level 2

Student Memory

Stores:

Preferences

Goals

Behavior

Level 3

Preparation Twin

Stores:

Knowledge

Mastery

Retention

Predictions
14. Tool Architecture

Agents never access databases directly.

They use tools.

Example

GetLearningGraphTool

GetWeakTopicsTool

GetRevisionBacklogTool

GetPYQInsightsTool

GetAssessmentHistoryTool

Benefits:

Security
Testing
Observability
15. Tool Registry

Every tool registered centrally.

Example

tool_registry

mentor_tools

assessment_tools

knowledge_tools

analytics_tools
16. LangGraph Architecture

Use LangGraph.

Reason:

State management
Agent routing
Persistence
Observability

Graph Example

User

 ↓

Supervisor

 ↓

Mentor Agent

 ↓

Generate Plan

 ↓

Save Plan

 ↓

Return Response
17. Shared State

Every workflow shares state.

GraphState

student_id

tenant_id

conversation_id

intent

messages

learning_graph

preparation_twin

tool_results

agent_outputs
18. AI Evaluation Framework

Most startups skip this.

Huge mistake.

Evaluate:

Hallucination Rate
Recommendation Quality
Plan Accuracy
Answer Evaluation Quality

Store scores.

Track over time.

19. Human-in-the-Loop

Critical for trust.

Faculty can override:

AI Scores

AI Plans

AI Recommendations

Overrides become training signals.

20. Prompt Architecture

Never hardcode prompts.

Store separately.

prompts/

mentor/

assessment/

knowledge/

current_affairs/

Version every prompt.

Example

mentor_v1

mentor_v2

mentor_v3
21. RAG Architecture

Knowledge Sources

NCERT

Laxmikanth

Spectrum

Current Affairs

Institute Material

Government Reports

PIB

PRS

Economic Survey

Pipeline

Upload

Chunk

Embed

Store

Retrieve

Answer
22. Hybrid Retrieval

Use:

Vector Search

+

Keyword Search

Why?

UPSC questions often contain:

names
acts
years
reports

Keyword search performs better.

23. AI Cost Optimization

Critical.

Use model tiers.

Simple Tasks:

GPT-4.1 Mini

Examples:

summaries
notes

Medium Tasks:

GPT-4.1

Examples:

mentor planning
explanations

Advanced Tasks:

GPT-5-class reasoning model

Examples:

mains evaluation
interview analysis
prediction review

(Use the strongest reasoning model available at implementation time.)

---

# 24. AI Explainability

Every recommendation must include:

```text
Why this recommendation?

Example:

Revise Fundamental Rights

Reason:

High PYQ frequency

Retention dropped to 54%

Exam in 120 days
25. Prediction Engine

Future moat.

Inputs:

Mastery

Retention

Assessment Scores

Revision Health

Study Consistency

Outputs:

Predicted Prelims Score

Predicted Mains Score

Risk Areas

Readiness Score
26. AI Observability

Track:

Agent

Prompt Version

Model

Latency

Cost

Tool Calls

Success Rate

Store every run.

27. MCP Integration Strategy

Future-ready architecture.

Supported MCP Servers:

Knowledge MCP

Provides:

syllabus
notes
books
PYQ MCP

Provides:

PYQs
trend analysis
Current Affairs MCP

Provides:

news
reports
summaries
Institute MCP

Provides:

batch data
analytics

This allows future interoperability with external AI ecosystems.

28. Future Agents

V2

Interview Agent

Career Agent

Essay Agent

Current Affairs Agent

V3

Research Agent

Policy Analysis Agent

Peer Learning Agent

Faculty Copilot Agent
29. Competitive Moat Hierarchy

Level 1

Chatbot

Easy.

Level 2

RAG

Moderate.

Level 3

Mentor Agent

Hard.

Level 4

Learning Graph

Very Hard.

Level 5

Preparation Twin

Extremely Hard.

Level 6

Prediction Engine

Elite Moat.

30. AI Rulebook

Rule 1

Learning Graph is truth.

Rule 2

Preparation Twin drives decisions.

Rule 3

Agents use tools.

Rule 4

Agents never directly query databases.

Rule 5

Every recommendation must be explainable.

Rule 6

Human overrides are valuable signals.

Rule 7

Optimize for student outcomes, not chat volume.