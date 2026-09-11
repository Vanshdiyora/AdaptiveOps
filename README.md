# AdaptiveOps

**AdaptiveOps** is a project-agnostic Agentic AI platform for investigating application incidents and identifying their likely root cause.

It combines **observability data + source code** to answer:

> **What is broken, where is the problem, why is it happening, and what code should be changed?**

## How It Works

```text
Repository Access ─────┐
                       ↓
Logs / Telemetry ──→ AdaptiveOps
                       ↓
                  Observation
                       ↓
                  Investigation
                       ↓
              Evidence Correlation
                       ↓
               Source Code Analysis
                       ↓
                Hypothesis Agent
                       ↓
              Hypothesis Validation
                       ↓
                  Root Cause
                       ↓
              Suggested Code Change
                       ↓
             Investigation Report
```

## Current Agents

* **Observation Agent** — collects and structures system observations.
* **Investigation Agent** — analyzes logs, exceptions, metrics, traces and relevant code.
* **Hypothesis Agent** — generates possible causes and supporting/contradicting evidence.
* **Validation** — evaluates hypotheses against available evidence.
* **Root Cause Analysis** — identifies the most likely source of the problem.

## Project Agnostic

AdaptiveOps is not tied to a specific programming language, cloud, or monitoring platform.

A new project mainly requires:

```text
1. Source repository access
2. Logs / observability access
```

Provider adapters can connect AdaptiveOps to different repositories and observability systems.

## Current Scope

**Focus:** Root-cause investigation and code-level analysis.

Not currently included:

* Automatic remediation
* Deployments or rollbacks
* Kubernetes/cloud modifications
* Autonomous code changes
* Automatic production actions

## Tech Stack

* Python
* LangChain
* MAQ AI (OpenAI-compatible) LLM
* Pydantic
* FastAPI
* LangGraph *(planned for orchestration)*

## Project Structure

```text
adaptiveops-agent/
├── app/
│   ├── agents/
│   ├── core/
│   ├── llm/
│   ├── services/
│   └── tools/
├── scripts/
│   └── debug_*.py
├── tests/
├── pyproject.toml
└── README.md
```

## Development Status

```text
[x] Project foundation
[x] Observation Agent
[x] Investigation Agent
[x] LLM integration
[x] Structured outputs
[x] Hypothesis Agent

[ ] Repository integration
[ ] Code analysis
[ ] Hypothesis validation
[ ] Root-cause selection
[ ] Investigation report
[ ] Workflow orchestration
```

## Philosophy

**Observe → Investigate → Reason → Validate → Identify Root Cause**

AdaptiveOps aims to turn:

> **"Something is broken."**

into:

> **"Here is where it broke, why it broke, and what should change."**
