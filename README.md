# AdaptiveOps — Self-Learning Agentic Platform for Autonomous Software Operations

## 1. Project Overview

**AdaptiveOps** is an Agentic AI platform designed to autonomously observe, investigate, diagnose, validate, remediate, and learn from software-system incidents.

The primary goal is to build an **AI-powered SRE/DevOps operations platform** that can understand an unfamiliar software system, continuously observe its behavior, detect abnormal conditions, investigate incidents, generate and validate competing root-cause hypotheses, safely recommend or execute remediation actions, verify recovery, and remember the outcome for future incidents.

Unlike a conventional monitoring dashboard or chatbot, AdaptiveOps is designed as an **operational decision-making system**.

The platform combines:

* Software/system discovery
* Logs
* Metrics
* Distributed traces
* Exceptions
* Health signals
* Deployment information
* Infrastructure state
* Configuration
* Historical incidents
* Operational memory
* LLM-based reasoning
* Deterministic anomaly detection
* Controlled experiments
* Policy-based remediation
* Automated verification
* Continuous learning

The system is designed to work across different projects and applications through a provider/adapter architecture.

---

# 2. Core Problem

Modern software systems generate huge amounts of operational data.

When an incident occurs, an SRE typically needs to manually:

1. Identify which service is affected.
2. Look at dashboards.
3. Search logs.
4. Inspect metrics.
5. Follow distributed traces.
6. Check exceptions.
7. Check recent deployments.
8. Investigate dependencies.
9. Form possible root-cause hypotheses.
10. Test those hypotheses.
11. Decide what action is safe.
12. Apply remediation.
13. Verify that the system recovered.
14. Document what happened.
15. Remember the incident for future troubleshooting.

This process is time-consuming and heavily dependent on human experience.

AdaptiveOps attempts to automate this operational reasoning loop.

---

# 3. Vision

The long-term vision is:

```text
Unknown Software System
        ↓
Discover
        ↓
Understand
        ↓
Observe
        ↓
Detect
        ↓
Investigate
        ↓
Generate Hypotheses
        ↓
Validate Hypotheses
        ↓
Identify Root Cause
        ↓
Plan Remediation
        ↓
Apply Safety Policy
        ↓
Execute Safely
        ↓
Verify Recovery
        ↓
Learn
        ↓
Improve Future Decisions
```

The platform should progressively become better at operating a specific software system as it observes more incidents.

---

# 4. Key Differentiator

AdaptiveOps is not intended to be just another LLM chatbot for DevOps.

The core idea is:

> **An adaptive operational intelligence system that learns how a specific software system behaves and uses previous operational experience to improve future incident investigation and remediation.**

The important differentiating capabilities are:

### 4.1 System-Specific Learning

Instead of treating every application the same way, AdaptiveOps builds knowledge about the specific system being operated.

For example:

```text
Order Service
 ├── Redis
 ├── PostgreSQL
 ├── Payment Service
 └── Inventory Service
```

The platform learns:

* Normal latency
* Normal error rate
* Normal resource usage
* Common dependencies
* Common failure patterns
* Deployment behavior
* Historical incidents
* Successful remediation actions

---

### 4.2 Competing Root-Cause Hypotheses

The system should not immediately assume one root cause.

For example:

```text
Incident:
Order Service error rate increased to 15%
```

The Hypothesis Agent may generate:

```text
H1: Redis connection exhaustion
H2: PostgreSQL latency
H3: Recent application deployment
H4: External payment dependency
```

Each hypothesis should contain:

* Confidence
* Supporting evidence
* Contradicting evidence
* Expected observations
* Predicted symptoms
* Validation strategy

---

### 4.3 Counterfactual Reasoning

AdaptiveOps should ask:

> "If this hypothesis were true, what else should I observe?"

Example:

```text
Hypothesis:
Redis connection exhaustion

Expected observations:

- Redis connection pool utilization ↑
- Redis timeout exceptions ↑
- Order-service latency ↑
- Redis dependency spans become slow
- Application CPU may remain normal
```

The agent then checks whether those predictions actually occur.

---

### 4.4 Controlled Experiments

Instead of relying only on LLM reasoning, AdaptiveOps can perform safe validation experiments.

Example:

```text
Compare:

Service Version 1
        vs
Service Version 2
```

If only version 2 exhibits the failure:

```text
Evidence → Deployment likely responsible
```

Experiments must be:

* Explicitly defined
* Typed
* Policy controlled
* Reversible where possible
* Limited in blast radius
* Verified after execution

---

### 4.5 Operational Memory

AdaptiveOps maintains memory of previous incidents.

Example:

```text
Incident #1042

Symptoms:
- Redis timeout
- High order latency
- Error rate > 10%

Root Cause:
Redis connection exhaustion

Action:
Restarted affected service

Result:
Recovered

Confidence:
0.91
```

A future incident with similar symptoms can retrieve this experience.

The system can then reason:

```text
Current Incident
       ↓
Similar Historical Incidents
       ↓
Previous Evidence
       ↓
Previous Root Causes
       ↓
Previous Successful Actions
       ↓
Improved Investigation
```

---

# 5. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │      User / SRE     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      Frontend       │
                         │ React / TypeScript  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    AdaptiveOps API  │
                         │      FastAPI        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Orchestrator     │
                         │     LangGraph       │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       Observation Agent    Investigation Agent    Hypothesis Agent
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                           Experiment Agent
                                    │
                                    ▼
                            Decision Agent
                                    │
                                    ▼
                             Policy Engine
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                         ▼                     ▼
                 Approval Required       Auto Approved
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                           Remediation Agent
                                    │
                                    ▼
                           Verification Agent
                                    │
                                    ▼
                             Learning Agent
                                    │
                                    ▼
                         Operational Memory
```

---

# 6. Observability Architecture

The first implementation uses **Application Insights** as the primary telemetry source.

The architecture must support both real telemetry and deterministic mock telemetry.

```text
                    Observability Layer
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
       Mock Provider             Azure Provider
             │                           │
             │                    Application Insights
             │                           │
             │                    Logs / Metrics / Traces
             │                           │
             └──────────────┬────────────┘
                            ▼
                  Observability Provider
                            │
                            ▼
                    Observation Service
                            │
                            ▼
                    Observation Agent
                            │
                            ▼
                  Normalized System State
```

The Observation Agent must not care whether the data came from:

```text
Mock
```

or:

```text
Application Insights
```

The provider abstraction handles this difference.

---

# 7. Current Observation POC

The first implementation focuses only on the **Observation phase**.

The current POC intentionally uses hardcoded telemetry.

The architecture should look as if the data is being retrieved from Application Insights, while the current provider returns deterministic mock telemetry.

This allows development of the complete agent architecture without requiring production telemetry during early development.

The configuration should support:

```env
OBSERVABILITY_MODE=mock
```

Later it can be changed to:

```env
OBSERVABILITY_MODE=azure
```

without changing the Observation Agent.

---

# 8. Observation Data

AdaptiveOps normalizes telemetry into a common schema.

## Logs

Example:

```text
INFO:
Order request received

WARNING:
Redis connection pool utilization above 80%

ERROR:
Redis connection timeout

ERROR:
Failed to process order
```

---

## Metrics

Example:

```text
Requests:
1250

Errors:
185

Error Rate:
14.8%

P50 Latency:
620 ms

P95 Latency:
2450 ms

CPU:
82.5%

Memory:
91.3%
```

---

## Traces

Example:

```text
CreateOrder
Duration: 2480ms
Status: ERROR

ValidateOrder
Duration: 125ms
Status: OK

CreateOrder
Duration: 2700ms
Status: ERROR
```

---

## Exceptions

Example:

```text
RedisTimeoutException:
Unable to acquire Redis connection

TimeoutError:
Redis operation exceeded timeout
```

---

# 9. Normalized Observation Model

All observability providers should return a common representation.

```text
ObservationSnapshot

├── timestamp
├── project_id
├── service
├── logs
├── metrics
├── traces
├── exceptions
└── health_status
```

This abstraction allows AdaptiveOps to support multiple observability systems in the future.

---

# 10. Observation Agent

The Observation Agent is responsible for determining the current state of a system.

It should:

1. Identify the target project.
2. Identify the target service.
3. Request telemetry from the observability provider.
4. Collect logs.
5. Collect metrics.
6. Collect traces.
7. Collect exceptions.
8. Calculate the current health state.
9. Produce a normalized `ObservationSnapshot`.

The Observation Agent should **not**:

* Perform remediation.
* Execute arbitrary commands.
* Make unrestricted infrastructure changes.
* Decide the root cause.
* Directly control Kubernetes.
* Directly modify production systems.

Its responsibility is:

> **Understand what is currently happening.**

---

# 11. Health Calculation

The initial POC uses deterministic health calculation.

Example:

```text
Error Rate >= 10%
        ↓
CRITICAL

Error Rate >= 5%
        ↓
DEGRADED

Exceptions detected
        ↓
DEGRADED

Otherwise
        ↓
HEALTHY
```

This logic should eventually evolve into a more sophisticated baseline/anomaly detection engine.

The LLM should not be responsible for calculating basic numerical health signals.

---

# 12. Future Baseline Learning

The platform should eventually learn normal behavior for each service.

Example:

```text
Order Service

Normal:
Error Rate: 0.5% - 2%
P95 Latency: 150 - 400ms
Memory: 45 - 70%
CPU: 30 - 65%
```

AdaptiveOps can then detect:

```text
Current:
Error Rate: 14.8%
P95: 2450ms
Memory: 91.3%
```

and determine that the system is behaving abnormally.

Possible baseline techniques:

* Rolling averages
* Standard deviation
* Percentiles
* EWMA
* Seasonal baselines
* Time-of-day baselines
* Deployment-aware baselines

---

# 13. Investigation Agent

Once an anomaly is detected, the Investigation Agent gathers evidence.

It should investigate:

```text
Logs
Metrics
Traces
Exceptions
Dependencies
Deployments
Infrastructure
Configuration
Historical incidents
```

The investigation should answer:

```text
What changed?

When did it change?

Which service is affected?

Which dependency is affected?

What telemetry changed?

What happened immediately before the incident?

Which signals are correlated?
```

The agent should produce structured evidence rather than an unstructured paragraph.

---

# 14. Hypothesis Agent

The Hypothesis Agent generates multiple possible explanations.

Example:

```text
Incident:
Order-service latency increased significantly.
```

Possible hypotheses:

```text
H1:
Redis connection exhaustion

H2:
Database performance degradation

H3:
Recent application deployment

H4:
External payment dependency latency
```

Each hypothesis should contain:

```text
Hypothesis
Confidence
Supporting Evidence
Contradicting Evidence
Predictions
Validation Plan
```

Example:

```json
{
  "hypothesis": "Redis connection exhaustion",
  "confidence": 0.84,
  "supporting_evidence": [
    "Redis timeout exceptions increased",
    "Connection pool utilization above 80%",
    "Redis spans are slow"
  ],
  "contradicting_evidence": [],
  "predictions": [
    "Redis dependency latency should be elevated",
    "Connection acquisition failures should increase"
  ]
}
```

---

# 15. Counterfactual Validation

For every important hypothesis, AdaptiveOps should determine what observations should exist if that hypothesis were true.

Example:

```text
H1:
Redis failure
```

Expected:

```text
Redis latency ↑
Redis errors ↑
Connection failures ↑
Order latency ↑
```

If these observations are not present:

```text
Hypothesis confidence ↓
```

If the observations are present:

```text
Hypothesis confidence ↑
```

This creates an evidence-driven investigation process.

---

# 16. Experiment Agent

The Experiment Agent validates high-value hypotheses using controlled experiments.

Examples:

```text
Compare service versions

Check dependency health

Query specific telemetry windows

Compare healthy vs unhealthy instances

Inspect resource usage

Perform safe synthetic requests

Compare deployment timestamps
```

Experiments must be safe.

The Experiment Agent must never directly execute arbitrary commands generated by an LLM.

Instead it should request typed operations.

Example:

```text
check_service_health(service_id)
compare_versions(version_a, version_b)
query_dependency_latency(dependency_id)
get_recent_deployment(service_id)
```

---

# 17. Decision Agent

The Decision Agent determines the best remediation strategy.

It should consider:

```text
Root Cause Confidence
+
Historical Success Rate
+
Action Risk
+
Blast Radius
+
Reversibility
+
Business Impact
+
Policy
```

Example:

```text
Root Cause:
Bad deployment

Confidence:
0.94

Action:
Rollback deployment

Risk:
Low

Reversible:
Yes

Blast Radius:
Single service
```

Therefore:

```text
Recommendation:
Rollback
```

---

# 18. Policy Engine

The Policy Engine is **deterministic**.

It should not rely entirely on an LLM to determine whether an action is safe.

Example policy:

```text
restart_service
    ↓
Allowed automatically
if:
    blast_radius <= 1 service
    AND
    service is non-critical
```

Another example:

```text
database_failover
    ↓
Approval required
```

Another:

```text
delete_production_resource
    ↓
Blocked
```

The policy engine returns:

```text
ALLOW
DENY
REQUIRES_APPROVAL
```

---

# 19. Remediation Agent

The Remediation Agent executes approved actions through controlled tools.

Examples:

```text
restart service

rollback deployment

scale service

clear cache

disable unhealthy instance

change configuration
```

The agent does not directly execute arbitrary shell commands.

Instead:

```text
LLM
 ↓
Typed Tool Request
 ↓
Policy Engine
 ↓
Permission Check
 ↓
Execution
```

This creates a safety boundary.

---

# 20. Verification Agent

After remediation, the Verification Agent checks whether the system actually recovered.

It should compare:

```text
Before remediation
        vs
After remediation
```

Example:

```text
Before:

Error Rate: 14.8%
P95: 2450ms
Memory: 91.3%

After:

Error Rate: 1.2%
P95: 320ms
Memory: 61%
```

Result:

```text
RECOVERED
```

If recovery does not occur:

```text
Verification Failed
        ↓
Investigation
        ↓
New Hypothesis
        ↓
New Validation
```

Therefore the workflow should support loops.

---

# 21. Learning Agent

After an incident is resolved, the Learning Agent creates an incident learning record.

Example:

```text
Incident ID:
INC-1042

Service:
order-service

Symptoms:
- High latency
- Redis timeout
- High error rate

Root Cause:
Redis connection exhaustion

Evidence:
- Redis connection utilization > 80%
- Redis timeout exceptions
- Slow Redis traces

Remediation:
Restart service

Result:
Recovered

Confidence:
0.93
```

This information becomes part of operational memory.

---

# 22. Operational Memory

Operational Memory is different from a normal documentation knowledge base.

### Knowledge Base

Contains static information:

```text
Architecture documentation
Runbooks
Policies
Service documentation
Deployment documentation
```

### Operational Memory

Contains learned experiences:

```text
Past incidents
Root causes
Evidence
Experiments
Remediation actions
Results
Failed actions
Successful actions
Confidence
```

The combination allows the system to reason using both:

```text
What the system SHOULD do
```

and:

```text
What actually worked before
```

---

# 23. Agent Orchestration

The system should use a state-machine-based orchestration architecture.

Recommended workflow:

```text
DETECTED
   ↓
OBSERVING
   ↓
INVESTIGATING
   ↓
HYPOTHESIS_GENERATED
   ↓
VALIDATING
   ↓
ROOT_CAUSE_IDENTIFIED
   ↓
ACTION_PLANNED
   ↓
POLICY_CHECK
   ↓
WAITING_FOR_APPROVAL
   ↓
REMEDIATING
   ↓
VERIFYING
   ↓
RESOLVED
   ↓
LEARNING
```

Failure path:

```text
VERIFYING
    ↓
Recovery Failed
    ↓
INVESTIGATING
```

This prevents the system from behaving like one giant uncontrolled agent.

---

# 24. Why LangGraph

LangGraph should be used for orchestration because AdaptiveOps requires:

* Stateful execution
* Conditional routing
* Loops
* Checkpoints
* Human approval
* Agent-to-agent state
* Failure recovery
* Long-running workflows

The individual agents remain focused on specific responsibilities.

LangGraph coordinates them.

---

# 25. LLM Responsibilities

The LLM should primarily handle:

```text
Reasoning
Hypothesis generation
Evidence interpretation
Investigation planning
Counterfactual reasoning
Experiment selection
Remediation explanation
Incident summarization
Learning record generation
```

The LLM should not be responsible for:

```text
Numerical metric calculations
Policy enforcement
Permission checks
Raw infrastructure access
Arbitrary shell execution
Safety decisions without deterministic validation
```

This creates a hybrid architecture:

```text
Deterministic Systems
+
LLM Reasoning
+
Typed Tools
+
Policy Engine
```

---

# 26. Tool Architecture

Agents should interact with infrastructure through typed tools.

Example:

```text
tools/
├── observability/
│   ├── provider.py
│   ├── application_insights.py
│   ├── mock_provider.py
│   └── azure_provider.py
│
├── infrastructure/
│   ├── kubernetes.py
│   └── azure.py
│
├── deployment/
│   └── azure_devops.py
│
├── experiment/
│   └── experiment_tools.py
│
└── memory/
    └── memory_tools.py
```

This provides a controlled interface between agents and external systems.

---

# 27. Provider Abstraction

The observability layer must use a provider abstraction.

```text
ObservabilityProvider
        │
        ├── MockApplicationInsightsProvider
        │
        └── AzureApplicationInsightsProvider
```

The Observation Agent only interacts with:

```text
ObservabilityProvider
```

It does not know whether the source is:

```text
Mock
Azure Application Insights
Prometheus
Datadog
OpenTelemetry
```

This makes AdaptiveOps extensible.

---

# 28. Current Mock Provider

During development, the mock provider returns deterministic telemetry.

Example incident:

```text
Service:
order-service
```

Telemetry indicates:

```text
Error Rate:
14.8%

P95 Latency:
2450ms

Memory:
91.3%

Redis:
Connection pool > 80%

Exceptions:
RedisTimeoutException
```

This creates a repeatable failure scenario for development and testing.

---

# 29. Azure Application Insights Provider

The production-oriented provider will eventually query Application Insights/Azure Monitor.

The provider should retrieve:

```text
Logs
Metrics
Traces
Exceptions
Requests
Dependencies
```

The provider should normalize the Azure telemetry into AdaptiveOps schemas.

The rest of the application should not depend directly on Application Insights-specific schemas.

---

# 30. Security Architecture

Security is a major requirement.

AdaptiveOps must follow the principle of least privilege.

Observation permissions should be separated from remediation permissions.

Example:

```text
Observation Identity

READ:
Logs
Metrics
Traces
Deployment information
Infrastructure state
```

Remediation identity:

```text
WRITE:
Restart
Rollback
Scale
Configuration changes
```

The LLM should never receive unrestricted credentials.

Secrets must never be hardcoded.

Environment variables or managed identity should be used.

Example:

```env
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_APPLICATION_INSIGHTS_RESOURCE_ID=
```

Production deployments should prefer managed identity or workload identity where available.

---

# 31. Project Discovery

Before AdaptiveOps can operate an unfamiliar system, it should discover its architecture.

Discovery sources include:

```text
Source Code
Docker
Docker Compose
Kubernetes
Helm
Cloud Resources
Application Insights
Configuration
Environment Variables
Network Information
Deployment Systems
```

For example:

```text
Frontend
   ↓
API Gateway
   ↓
Order Service
   ├── PostgreSQL
   └── Redis
```

AdaptiveOps should build a system graph:

```text
Service
Dependency
Infrastructure
Telemetry
Deployment
```

Each discovered relationship should ideally have a confidence score.

---

# 32. Example End-to-End Incident

Consider:

```text
Order Service v2
```

is deployed.

Shortly afterward:

```text
Memory ↑
Latency ↑
Errors ↑
Redis timeouts ↑
```

AdaptiveOps observes:

```text
Error Rate = 14.8%
P95 = 2450ms
Memory = 91.3%
```

Investigation discovers:

```text
Incident started 3 minutes after deployment.
```

Hypothesis Agent generates:

```text
H1: Memory leak introduced by deployment
H2: Redis failure
H3: Database regression
H4: External dependency failure
```

Counterfactual reasoning determines:

```text
H1 predicts:
Memory ↑
Latency ↑
Errors ↑
Deployment correlation
```

Telemetry matches.

Experiment:

```text
Compare v1 vs v2
```

Result:

```text
v1 → healthy
v2 → unhealthy
```

Root cause confidence:

```text
94%
```

Decision:

```text
Rollback v2
```

Policy:

```text
ALLOW
```

Remediation:

```text
Rollback deployment
```

Verification:

```text
Error Rate:
14.8% → 1.1%

P95:
2450ms → 310ms

Memory:
91.3% → 59%
```

Incident resolved.

Learning Agent stores:

```text
Deployment regression → rollback → successful recovery
```

Future incidents can retrieve this experience.

---

# 33. Project Structure

```text
adaptiveops-agent/
│
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── enums.py
│   │   ├── models.py
│   │   └── exceptions.py
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── router.py
│   │   ├── workflow.py
│   │   └── checkpoints.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   │
│   │   ├── base/
│   │   │   ├── __init__.py
│   │   │   └── base_agent.py
│   │   │
│   │   ├── observation/
│   │   ├── investigation/
│   │   ├── hypothesis/
│   │   ├── experiment/
│   │   ├── decision/
│   │   ├── remediation/
│   │   ├── verification/
│   │   └── learning/
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   │
│   │   ├── observability/
│   │   │   ├── __init__.py
│   │   │   ├── provider.py
│   │   │   ├── application_insights.py
│   │   │   ├── mock_provider.py
│   │   │   └── azure_provider.py
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── kubernetes.py
│   │   │   └── azure.py
│   │   │
│   │   ├── deployment/
│   │   │   └── azure_devops.py
│   │   │
│   │   ├── experiment/
│   │   │   └── experiment_tools.py
│   │   │
│   │   └── memory/
│   │       └── memory_tools.py
│   │
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── policy_engine.py
│   │   ├── rules.py
│   │   └── permissions.py
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── incident_memory.py
│   │   ├── vector_memory.py
│   │   ├── models.py
│   │   └── repository.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── provider.py
│   │   ├── prompts.py
│   │   └── structured_output.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── observation_service.py
│       ├── incident_service.py
│       ├── telemetry_service.py
│       ├── hypothesis_service.py
│       └── remediation_service.py
│
├── tests/
│   ├── __init__.py
│   ├── agents/
│   │   ├── test_observation.py
│   │   ├── test_investigation.py
│   │   ├── test_hypothesis.py
│   │   ├── test_experiment.py
│   │   ├── test_decision.py
│   │   ├── test_remediation.py
│   │   ├── test_verification.py
│   │   └── test_learning.py
│   │
│   ├── orchestration/
│   │   └── test_workflow.py
│   │
│   └── policies/
│       └── test_policy_engine.py
│
└── scripts/
        ├── run_agent.py
    └── simulate_incident.py
```

---

# 34. Technology Stack

## Backend

```text
Python
FastAPI
Pydantic
Pydantic Settings
```

## Agent Orchestration

```text
LangGraph
```

## LLM

The system should support a configurable LLM provider.

The LLM should support:

* Tool calling
* Structured output
* Reasoning
* JSON/schema-constrained responses

---

## Observability

Initial:

```text
Azure Application Insights
```

Future:

```text
OpenTelemetry
Prometheus
Grafana
Loki
Tempo
Datadog
CloudWatch
```

---

## Infrastructure

Potential deployment targets:

```text
Docker
Kubernetes
Azure
kind
```

---

## Storage

Initial:

```text
PostgreSQL
```

Future:

```text
Vector Database
pgvector
Redis
```

---

# 35. Development Strategy

AdaptiveOps should be developed incrementally.

Do not implement the entire autonomous system at once.

## Phase 1 — Observation

Current phase.

Implement:

```text
Mock telemetry
        ↓
Provider
        ↓
Observation Service
        ↓
Observation Agent
        ↓
Observation Snapshot
```

Validate:

```text
Logs
Metrics
Traces
Exceptions
Health
```

---

## Phase 2 — Real Application Insights

Replace:

```text
Mock Provider
```

with:

```text
Azure Application Insights Provider
```

without changing the Observation Agent.

Validate real:

```text
KQL
Logs
Requests
Exceptions
Dependencies
Telemetry
```

---

## Phase 3 — Baseline and Anomaly Detection

Implement:

```text
Historical telemetry
        ↓
Baseline
        ↓
Current telemetry
        ↓
Deviation
        ↓
Anomaly
```

---

## Phase 4 — Investigation Agent

Implement:

```text
Incident
 ↓
Evidence Collection
 ↓
Correlation
 ↓
Timeline
```

---

## Phase 5 — Hypothesis Agent

Implement:

```text
Evidence
 ↓
Multiple Hypotheses
 ↓
Predictions
 ↓
Confidence
```

---

## Phase 6 — Experiment Agent

Implement controlled hypothesis validation.

---

## Phase 7 — Decision and Policy

Implement:

```text
Root Cause
 ↓
Candidate Actions
 ↓
Risk Assessment
 ↓
Policy
 ↓
Approval
```

---

## Phase 8 — Remediation

Implement safe typed remediation tools.

---

## Phase 9 — Verification

Implement automated recovery verification.

---

## Phase 10 — Operational Memory

Store:

```text
Incident
Evidence
Hypotheses
Experiments
Root Cause
Action
Outcome
```

---

## Phase 11 — Adaptive Learning

Use historical incidents to improve:

```text
Hypothesis ranking
Investigation strategy
Experiment selection
Remediation recommendations
```

---

# 36. Safety Principles

AdaptiveOps must follow these principles:

### Principle 1 — Read Before Write

The system should observe and investigate before making changes.

### Principle 2 — Evidence Before Action

Remediation should require sufficient evidence.

### Principle 3 — Least Privilege

Agents receive only the permissions required for their job.

### Principle 4 — Typed Tools

LLMs interact with infrastructure through predefined tools.

### Principle 5 — Policy Enforcement

Every remediation action passes through the policy engine.

### Principle 6 — Reversible Actions

Prefer reversible remediation.

### Principle 7 — Limited Blast Radius

Prefer actions affecting the smallest possible scope.

### Principle 8 — Verification

Every remediation must be followed by verification.

### Principle 9 — Human Approval

High-risk actions require human approval.

### Principle 10 — Auditability

Every agent decision and action should be recorded.

---

# 37. State Model

The central agent state should contain information such as:

```text
incident_id
project_id
service
status
system_state
observations
evidence
hypotheses
experiments
root_cause
proposed_action
policy_result
remediation_result
verification_result
similar_incidents
learning_record
errors
messages
```

This state is passed between workflow nodes.

---

# 38. Example State Transition

```text
{
    "incident_id": "INC-1001",
    "service": "order-service",
    "status": "INVESTIGATING",

    "observations": [...],

    "evidence": [...],

    "hypotheses": [...],

    "root_cause": null,

    "proposed_action": null,

    "policy_result": null,

    "remediation_result": null,

    "verification_result": null
}
```

As the workflow progresses, fields are populated.

---

# 39. Testing Strategy

The project should have tests for every major component.

### Unit Tests

```text
Observation
Providers
Health calculation
Hypothesis scoring
Policy engine
Tool validation
Verification logic
Memory
```

### Integration Tests

```text
Application Insights provider
Database
LLM
LangGraph workflow
Kubernetes tools
```

### Simulation Tests

The platform should be able to simulate incidents.

Example:

```text
simulate_incident.py
```

Scenario:

```text
Deploy bad version
 ↓
Latency increases
 ↓
Memory increases
 ↓
Errors increase
 ↓
Agent investigates
 ↓
Rollback
 ↓
Verify recovery
```

---

# 40. Example Commands

The project uses `uv` for Python environment and dependency management.

Create/synchronize environment:

```powershell
uv sync
```

Add dependencies:

```powershell
uv add pydantic pydantic-settings
```

Run observation:

```powershell
uv run python -m scripts.run_agent observation
```

Run observation, incident detection, and investigation (default):

```powershell
uv run python -m scripts.run_agent
```

The explicit `investigation` subcommand runs the same complete workflow.

## LangChain, LangGraph, and Groq Investigation

LangChain provides the chat-model abstraction, prompt composition, and Pydantic
structured output. Groq is the current model provider and can be replaced behind
the centralized factory in `app/llm/provider.py`. LangGraph coordinates the
investigation lifecycle without combining AdaptiveOps agents into one agent.

The current graph is:

```text
START
        -> load_incident
        -> collect_evidence
        -> prepare_investigation_context
        -> llm_investigate
        -> validate_investigation
        -> END

On model or validation failure:
        -> investigation_failed
        -> END
```

Telemetry collection, metric and health calculations, threshold detection,
incident creation, evidence extraction, and evidence-reference validation remain
deterministic. The read-only Investigation Agent receives normalized evidence and
uses the LLM only for correlation, timeline and dependency reasoning, summary,
and uncertainty reporting. It has no shell or infrastructure tools.

Copy `.env.example` to `.env`, then set a Groq key and model locally:

```powershell
Copy-Item .env.example .env
$env:GROQ_API_KEY="your-api-key"
$env:GROQ_MODEL="qwen/qwen3.6-27b"
$env:GROQ_TEMPERATURE="0.0"
uv sync
uv run python -m scripts.run_agent
```

The environment variables override `.env`. Never commit `.env` or print the API
key. `GROQ_MODEL` is centralized, so switching an unavailable model requires only
configuration. Observation can run without Groq:

```powershell
uv run python -m scripts.run_agent observation
```

Current limitations: the investigation depends on the evidence in one observation
snapshot, performs no retries beyond the configured Groq client retry, and does
not execute remediation. The next graph phase will consume `InvestigationResult`
to generate multiple competing hypotheses with supporting and contradicting
evidence, predictions, confidence, and validation strategies.

---

# 41. Configuration

Example:

```env
OBSERVABILITY_MODE=mock

OBSERVATION_WINDOW_MINUTES=10

AZURE_APPLICATION_INSIGHTS_RESOURCE_ID=

AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
```

Development:

```env
OBSERVABILITY_MODE=mock
```

Azure:

```env
OBSERVABILITY_MODE=azure
```

The agent code should remain unchanged.

---

# 42. Important Architectural Rule

The following separation must be maintained:

```text
Agents
    ↓
Services
    ↓
Tools / Providers
    ↓
External Systems
```

Agents should not directly contain:

```text
Azure SDK calls
Kubernetes API calls
Database queries
Shell commands
```

Instead:

```text
Agent
 ↓
Service
 ↓
Typed Tool
 ↓
External System
```

This makes the platform easier to test, secure, and extend.

---

# 43. What AdaptiveOps Should Ultimately Become

The final platform should behave like an autonomous SRE assistant/operator.

A user should be able to provide:

```text
Project:
Commerce Platform
```

AdaptiveOps should discover:

```text
Services
Dependencies
Infrastructure
Telemetry
Deployments
```

Then continuously understand:

```text
What is normal?
What is changing?
What is broken?
Why is it broken?
What evidence supports the explanation?
What experiment can prove it?
What action is safest?
Did the action work?
What did we learn?
```

The ultimate loop is:

```text
                  ┌─────────────────────────────┐
                  │                             │
                  │       Software System       │
                  │                             │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                              OBSERVE
                                 │
                                 ▼
                               DETECT
                                 │
                                 ▼
                            INVESTIGATE
                                 │
                                 ▼
                           HYPOTHESIZE
                                 │
                                 ▼
                              EXPERIMENT
                                 │
                                 ▼
                              DECIDE
                                 │
                                 ▼
                               POLICY
                                 │
                                 ▼
                             REMEDIATE
                                 │
                                 ▼
                              VERIFY
                                 │
                                 ▼
                               LEARN
                                 │
                                 ▼
                         OPERATIONAL MEMORY
                                 │
                                 └───────────────┐
                                                 │
                                                 ▼
                                      Better Future Decisions
```

---

# 44. Success Criteria

AdaptiveOps will be considered successful when it can demonstrate an end-to-end incident lifecycle:

```text
1. Discover system
2. Observe telemetry
3. Detect abnormal behavior
4. Investigate evidence
5. Generate multiple root-cause hypotheses
6. Validate hypotheses
7. Select the most likely root cause
8. Recommend a remediation
9. Apply policy checks
10. Execute an approved action
11. Verify recovery
12. Store incident knowledge
13. Use that knowledge during a future similar incident
```

The final demonstration should show that AdaptiveOps is not merely generating an explanation with an LLM.

It should demonstrate an actual **closed-loop operational intelligence system**.

---

# 45. Project Philosophy

AdaptiveOps follows one fundamental principle:

> **Observe first. Reason from evidence. Validate assumptions. Act within policy. Verify the outcome. Learn from the result.**

The LLM provides reasoning capability.

Deterministic systems provide measurement, safety, policy, and execution boundaries.

Together they form an adaptive Agentic SRE platform.
