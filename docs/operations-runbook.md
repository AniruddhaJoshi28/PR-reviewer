# Operations Runbook & Policy Governance

## 1. Handling Policy Gate Decisions

| Decision | Meaning | Action Required |
| :--- | :--- | :--- |
| `PASS` | All automated checks passed; low risk | Automated CI completion; ready for standard PR review |
| `HUMAN_APPROVAL_REQUIRED` | Medium or High risk detected | Requires minimum 1 or 2 authorized human sign-offs in Jenkins |
| `BLOCKED` | Mandatory scanner failure or high vulnerability | Author must remediate findings; build fails closed |
| `INCOMPLETE` | Stale commit SHA or missing evaluations | Re-trigger pipeline on verified HEAD commit |

## 2. Emergency Policy Overrides
If an urgent production fix must bypass a false-positive block:
1. Authorized roles: `security-lead`, `tech-lead`, `release-manager`.
2. Must provide explicit business rationale.
3. Override audit record is permanently embedded in `policy-decision.json`.
