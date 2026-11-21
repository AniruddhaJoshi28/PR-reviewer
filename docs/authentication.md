# Authentication, Secrets Isolation & Transmission Policy

## 1. Zero Enterprise Credential Leakage
- URL basic auth credentials (`http://user:pass@host`) are automatically redacted via `sanitize_url`.
- Scanners replace discovered credentials with `***REDACTED***` before serializing into reports.

## 2. AI Transmission Disabled by Default
- The platform defaults to `AI_PROVIDER=offline` and `ENABLE_EXTERNAL_AI=false`.
- External model transmission (OpenAI Codex or Anthropic Claude) requires explicit administrative enablement.
- All AI reviewers operate in strictly read-only mode.
