# Autonomous Business Intelligence & Action Platform

An AI-powered business operations platform that converts natural-language business questions into verified, evidence-based analysis and actionable recommendations.

The platform combines:

- Natural-language-to-SQL
- SQL safety and schema validation
- Business semantic validation
- Numerical verification
- Retrieval-Augmented Generation (RAG)
- AI-assisted business reasoning
- Multi-step analysis orchestration
- Diagnostic investigation
- Recommendation generation
- Human approval workflows
- Action simulation
- Audit logging
- Operational monitoring
- Automated testing

> **Safety-first design:** The platform does not execute real business actions. Recommendations require explicit human approval and are only simulated after approval.

---

## Problem

Business teams often need answers to questions such as:

- "What was our revenue in May 2025?"
- "Which region generated the highest revenue?"
- "Why did revenue change compared with the previous month?"
- "Which products contributed most to the change?"

Traditional business intelligence workflows can require analysts to manually write SQL, inspect dashboards, investigate supporting evidence, and translate findings into actions.

This project explores how an AI-powered business operations system can automate much of that analytical workflow while keeping database evidence, verification, and human approval at the center.

---

## What the Platform Does

A user submits a business question in natural language.

```text
"What was the revenue in May 2025?"


The system processes the request through an orchestrated pipeline:
User Question
      ↓
Analysis Planner
      ↓
Workflow Selection
      ↓
Natural Language → SQL
      ↓
SQL Safety Validation
      ↓
Schema Validation
      ↓
Business Semantic Validation
      ↓
Database Execution
      ↓
Evidence Formatting
      ↓
RAG Knowledge Retrieval
      ↓
AI Reasoning
      ↓
Numerical Verification
      ↓
Evidence Package
      ↓
Recommendation Engine
      ↓
Human Approval Gate
      ↓
Action Simulation
      ↓
Audit Logging + Monitoring



ARCHITECTURE

┌───────────────────────────────┐
│        React Dashboard        │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│          FastAPI API          │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│     Business Orchestrator     │
└───────────────┬───────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
┌──────────────┐  ┌───────────────┐
│ AI Analysis  │  │  Diagnostic   │
│   Planner    │  │   Executor    │
└──────┬───────┘  └───────┬───────┘
       │                  │
       └────────┬─────────┘
                ▼
      ┌───────────────────┐
      │ SQL / Database    │
      │ RAG / Evidence    │
      │ ML / Analytics    │
      └─────────┬─────────┘
                ▼
      ┌───────────────────┐
      │ AI Reasoning      │
      │ + Verification    │
      └─────────┬─────────┘
                ▼
      ┌───────────────────┐
      │ Recommendation    │
      │ Engine            │
      └─────────┬─────────┘
                ▼
      ┌───────────────────┐
      │ Human Approval    │
      └─────────┬─────────┘
                ▼
      ┌───────────────────┐
      │ Action Simulator  │
      └─────────┬─────────┘
                ▼
      ┌───────────────────┐
      │ Audit + Monitoring│
      └───────────────────┘

Key Engineering Features
1. Natural Language → SQL

The platform accepts business questions in natural language and generates SQL queries against the business database.

Example:
Business question:
"What was the revenue in May 2025?"

Generated analysis:
SELECT SUM(o.total_amount)
FROM aibusinessanalytics.orders o
WHERE o.order_date >= '2025-05-01'
  AND o.order_date < '2025-06-01';

2. SQL Safety Validation

Generated SQL is validated before execution.

The validator prevents unsafe operations such as:
INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
CREATE
GRANT
REVOKE
MERGE

3. Schema Validation

The generated query is checked against the expected database schema before execution.

This helps detect:

Invalid table names
Invalid column references
Incorrect schema references
Missing table references
4. Business Semantic Validation

Syntactically valid SQL is not necessarily business-correct.

The platform therefore checks whether the generated query matches the intended business meaning.

For example:Revenue

is calculated from:
orders.total_amount

while product-level revenue uses:
order_items.quantity × order_items.price

This prevents the AI from silently using the wrong business metric.
5. Numerical Verification

AI-generated explanations are checked against trusted database results.

For example, if the database returns:

133018981.00

the verification layer accepts equivalent presentation formats such as:

₹133,018,981.00
₹13,30,18,981.00

but rejects incorrect numerical claims.

6. RAG-Based Business Reasoning

The platform retrieves relevant business knowledge from internal documentation before generating reasoning.

Knowledge sources include:

Business glossary
Business policies
Investigation guidelines

Database results remain the authoritative source for numerical facts.

The RAG layer provides business context rather than replacing database evidence.

7. Multi-Step Analysis

Different questions are routed to different analytical workflows.

Supported workflows include:

simple_factual
trend
comparison
diagnostic

A diagnostic question can trigger a multi-step investigation across:

Overall revenue
Regional performance
Product performance
Return rates
Supporting operational evidence
8. Evidence Package

The system creates a structured evidence package containing:

Business question
Analysis plan
Workflow
Database execution result
Formatted SQL evidence
AI reasoning
Numerical verification
Final verification status

This creates an auditable boundary between raw database evidence and AI-generated interpretation.

9. Recommendation Engine

Verified analysis can be converted into a structured recommendation containing:

Observed fact
Business implication
Recommended action
Reason
Evidence confidence
Recommendation confidence

Recommendations are marked:

READY_FOR_REVIEW

rather than being automatically executed.

10. Human Approval

Every recommendation passes through a human approval gate.

Possible states:

PENDING
APPROVED
REJECTED

This provides a human control point before any simulated operational action.

11. Action Simulation

After approval, the system can simulate what business action would have been taken.

The simulator explicitly records:

simulation_only = true
real_action_executed = false

No real customer communication, database mutation, or external business operation is performed.
12. Audit Logging

Important pipeline events are recorded as JSON Lines.

Examples include:

ANALYSIS_STARTED
RECOMMENDATION_CREATED
APPROVAL_REQUESTED
ACTION_SIMULATED
ANALYSIS_COMPLETED

This provides an audit trail for the AI decision workflow.

13. Monitoring

The platform tracks operational metrics such as:

Total analysis runs
Successful runs
Failed runs
Verification failures
Recommendation count
Approval requests
Simulated actions
Workflow distribution
Average execution time
Example Analysis

For the synthetic NovaMart dataset, the platform can answer:

"What was the revenue in May 2025?"

with verified database evidence.

Example result:

Revenue in May 2025:
₹13,30,18,981.00

The response is then numerically verified before being included in the final evidence package.

Technology Stack
Backend
Python
FastAPI
SQLAlchemy
PostgreSQL
AI / ML
Ollama
Qwen2.5 1.5B
Sentence Transformers
FAISS
Scikit-learn
Frontend
React
Vite
JavaScript
CSS
Engineering
Pytest
Git
GitHub
JSON Lines audit logging

Project Structure
Autonomous-Business-Intelligence-Action-Platform/
│
├── ai/
│   ├── orchestrator.py
│   ├── business_pipeline.py
│   ├── analysis_planner.py
│   ├── analysis_executor.py
│   ├── diagnostic_executor.py
│   ├── nl_to_sql.py
│   ├── nl_to_sql_service.py
│   ├── sql_validator.py
│   ├── schema_validator.py
│   ├── business_semantic_validator.py
│   ├── sql_executor.py
│   ├── numerical_verifier.py
│   ├── recommendation_engine.py
│   ├── human_approval.py
│   ├── action_simulator.py
│   ├── evidence_package.py
│   ├── audit_logger.py
│   └── monitoring.py
│
├── analytics/
│
├── api/
│   └── main.py
│
├── data/
│
├── frontend/
│
├── knowledge/
│   ├── business_glossary.md
│   ├── business_policies.md
│   └── investigation_guidelines.md
│
├── rag/
│   ├── rag_engine.py
│   ├── reasoning.py
│   ├── evidence_loader.py
│   └── evidence_formatter.py
│
├── tests/
│   ├── test_sql_validator.py
│   ├── test_schema_validator.py
│   ├── test_business_semantic_validator.py
│   ├── test_numerical_verifier.py
│   ├── test_human_approval_and_action.py
│   └── test_audit_and_monitoring.py
│
├── .gitignore
└── README.md

Testing

The project currently includes automated tests covering the core reliability and control layers.

49 passed

Test coverage includes:

SQL validation
Schema validation
Business semantic validation
Numerical verification
Human approval
Action simulation
Audit logging
Monitoring
Safety and Design Principles

The project follows several principles for trustworthy AI business automation:

Database evidence is authoritative for numerical facts.
Generated SQL is validated before execution.
Business semantics are checked separately from SQL syntax.
AI-generated numerical claims are verified.
Business knowledge is retrieved through RAG rather than invented.
Observed facts are separated from possible explanations.
Recommendations require human approval.
Operational actions are simulation-only.
Important workflow events are auditable.
Monitoring metrics are collected throughout the pipeline.
Project Status

The core platform is implemented and tested.

Current status:
AI analysis pipeline        ✓
Natural language → SQL      ✓
SQL validation              ✓
Schema validation           ✓
Semantic validation         ✓
Numerical verification      ✓
RAG reasoning               ✓
Multi-step orchestration    ✓
Diagnostic investigation    ✓
Evidence packages           ✓
Recommendation engine       ✓
Human approval              ✓
Action simulation           ✓
Audit logging               ✓
Monitoring                  ✓
Automated tests             ✓
React dashboard             ✓


Disclaimer

This project uses a synthetic business dataset for demonstration and portfolio purposes.

The action layer is intentionally simulation-only and does not perform real business operations.
