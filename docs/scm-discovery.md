# SCM Discovery & Provider Adapter Specification

## 1. Provider Resolution Logic
The platform uses multi-variable scoring to identify the hosting Git provider:
- **GitHub / GitHub Enterprise**: Matches `github.com` or `ghe` in `GIT_URL` or `CHANGE_URL`, plus `GITHUB_ACTIONS` or `CHANGE_ID`.
- **GitLab**: Matches `gitlab.com` or `gitlab` in URLs, plus `GITLAB_CI` or `CI_MERGE_REQUEST_IID`.
- **Bitbucket**: Matches `bitbucket.org` or `bitbucket` in URLs, plus `BITBUCKET_BUILD_NUMBER`.
- **Azure DevOps**: Matches `dev.azure.com` or `visualstudio.com`, plus `TF_BUILD`.
- **Generic Git (Fallback)**: When signals are below threshold (0.4), platform defaults to provider-neutral mode.

## 2. Inconclusive Detection Handling
When running under an unknown or on-prem Git provider without API integration:
1. Review and evaluation execute locally in Jenkins without interruption.
2. Reports and SARIF artifacts are archived in Jenkins.
3. Remote PR comment and commit status publishing are marked as unavailable.
4. The system **never claims** that remote merge is blocked when remote provider enforcement is unverified.
