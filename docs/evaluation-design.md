# Evaluation Benchmark Design & Scientific Methodology

## 1. Ground Truth Fixture Suite
Located in `evaluations/fixtures/` and annotated in `evaluations/ground_truth/labels.json`:
- `sql_injection.py`: Raw string SQL injection
- `auth_bypass.py`: Administrative authorization omission
- `hardcoded_secret.py`: Exposed cloud tokens
- `broken_api_contract.py`: Missing mandatory schema fields
- `incorrect_business_logic.py`: Off-by-one bracket pricing bug
- `concurrency_defect.py`: Unsynchronized state modification
- `unsafe_infra_change.py`: Security group opening `0.0.0.0/0`
- `prompt_injection.py`: Jailbreak instruction injection
- `failing_test.py`: Broken test assertion
- `benign_docs_update.md`: Pure documentation update (control)
- `false_positive_trap.py`: Safe code with suspicious variable names (control)

## 2. Benchmark Metrics
The runner computes:
- Precision, Recall, F1 Score
- Severity-Weighted Recall (prioritizing HIGH and MEDIUM risk issues)
- High-Risk False Negatives (must be 0 for security release gate)
- False Positive Rate
- Hallucinated Findings Rate
- Mean Review Latency and Token Usage
