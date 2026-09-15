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

## Local Repository Semantic Search

Repository investigation includes an optional, dependency-free semantic search
fallback based on local TF-IDF and cosine similarity over indexed source
symbols. It does not send source code to an external service and does not
require an API key, vector database, or network access.

Enable it with:

```text
REPOSITORY_PATH=C:\path\to\repository
REPOSITORY_ENABLE_SEMANTIC_SEARCH=true
```

Exact stack-trace, exception, message, operation, and identifier searches are
still preferred. Semantic search is used when exact search cannot resolve a
primary location.

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
├── .env.example
├── .gitignore
├── .python-version
├── main.py
├── pyproject.toml
├── requirements.txt
├── uv.lock
├── README.md
├── .vscode/
│   └── launch.json
├── adaptiveops_agent.egg-info/
│   ├── dependency_links.txt
│   ├── PKG-INFO
│   ├── requires.txt
│   ├── SOURCES.txt
│   └── top_level.txt
├── app/
│   ├── agents/
│   │   ├── investigation/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── graph.py
│   │   │   └── state.py
│   │   └── observation/
│   │       ├── __init__.py
│   │       ├── agent.py
│   │       ├── prompts.py
│   │       └── schemas.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── enums.py
│   │   ├── exceptions.py
│   │   ├── incident_models.py
│   │   ├── models.py
│   │   └── state.py
│   ├── detection/
│   │   ├── __init__.py
│   │   ├── detection.py
│   │   └── rules.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── prompts.py
│   │   ├── provider.py
│   │   └── structured_output.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── incident_service.py
│   │   ├── investigation_service.py
│   │   ├── observation_service.py
│   │   └── repository/
│   │       ├── __init__.py
│   │       ├── interface.py
│   │       └── local.py
│   └── tools/
│       ├── observability/
│       │   ├── __init__.py
│       │   ├── application_insights.py
│       │   ├── azure_provider.py
│       │   ├── logs.py
│       │   ├── metrics.py
│       │   ├── mock_provider.py
│       │   ├── provider.py
│       │   └── traces.py
│       └── repository/
│           ├── __init__.py
│           ├── chunker.py
│           ├── context.py
│           ├── embeddings.py
│           ├── fusion.py
│           ├── indexer.py
│           ├── investigator.py
│           ├── qdrant_store.py
│           ├── reranker.py
│           ├── schemas.py
│           ├── search.py
│           └── stacktrace.py
├── scripts/
│   ├── debug_experiment.py
│   ├── debug_investigation.py
│   ├── debug_repository.py
│   ├── run_agent.py
│   ├── run_hypothesis.py
│   └── simulate_incident.py
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
