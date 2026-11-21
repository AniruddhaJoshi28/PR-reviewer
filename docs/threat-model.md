# Security Threat Model & Defense Architecture

## 1. Threat Vectors Addressed
1. **Malicious PR Prompt Injection**: PR descriptions or comments attempting to instruct the reviewer to approve. *Mitigation*: Instruction boundary wrappers in prompts, deterministic classification triggers `RULE_HIGH_PROMPT_INJECTION`, fail-closed policy.
2. **Untrusted Code Execution in CI**: PR-controlled build scripts attempting to harvest Jenkins credentials. *Mitigation*: Unit tests run in `--network=none` ephemeral container with no bound credentials.
3. **Subprocess / Shell Injection**: Malicious branch names containing `;` or `$()`. *Mitigation*: All subprocess calls use list arguments without `shell=True`.
4. **Stale Commit Tampering**: Approvals applied to prior commits reused on new malicious commits. *Mitigation*: Immutable SHA verification validates current git HEAD matches evaluated HEAD.
5. **AI Hallucinations**: Model invent non-existent file paths or line numbers. *Mitigation*: `EvidenceValidator` verifies all findings verbatim against raw patch snippets.
