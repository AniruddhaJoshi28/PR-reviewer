# System Architecture & Technical Specification

The **Jenkins Agentic PR Review Platform** is an enterprise-oriented, Git-provider-agnostic code review and security evaluation engine native to Jenkins CI/CD.

```
Unknown Git Provider (GitHub / GitLab / Bitbucket / Azure DevOps / Generic)
    │
    ▼
Existing Jenkins Multibranch SCM Trigger
    │
    ▼
Trusted Jenkins Orchestrator
    ├── SCM Metadata Discovery (Multi-variable detection)
    ├── Immutable Base/Head SHA Verification (Anti-stale gate)
    ├── Isolated CI Worker (Linting, unit tests, no credentials)
    ├── Deterministic Risk Classifier (LOW / MEDIUM / HIGH)
    │     ├── LOW  ➔ 1 Reviewer (No debate)
    │     ├── MED  ➔ 4 Agents (Correctness, Maintainability, Challenger, Judge)
    │     └── HIGH ➔ 6 Agents (Correctness, Security, Data Contract, Infra, Challenger, Judge)
    ├── Security Scanners (Semgrep, Gitleaks, pip-audit: PASS/FAIL/NOT_RUN/ERROR/MOCK)
    ├── Evidence Validator (Hallucination rejection against raw diff)
    ├── Deterministic Policy Engine (Fail-closed policy.yaml)
    └── Jenkins Artifact Archiving (review.json, review.md, review.sarif, tests.xml, policy-decision.json)
    │
    ▼
Optional Git Provider Adapter (Commit Status & Idempotent Comments)
    │
    ▼
Mandatory Human Approval Gate (Two-person rule for HIGH risk)
```

## Security Boundaries

### 1. Trusted Orchestration vs Untrusted Worker Isolation
Untrusted PR code (including test files and build scripts) runs strictly in an ephemeral container with `--network=none` and without access to Jenkins credentials or AI model API keys.

### 2. Scanner Failure Semantics
In production mode, a scanner that fails or is not installed is marked `NOT_RUN`. Mandatory scanners marked `NOT_RUN` fail-closed and block the policy gate. Mock results (`MOCK_PASS` / `MOCK_FAIL`) are accepted only when running in explicit `--offline` demonstration mode.

### 3. Fail-Closed Policy Engine
The policy engine enforces versioned organization rules (`config/policy.yaml`). If any mandatory check fails, or if high-severity security vulnerabilities are present, the decision is `BLOCKED`.
