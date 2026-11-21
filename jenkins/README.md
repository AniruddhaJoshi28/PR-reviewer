# Jenkins Integration & Setup Guide

This directory contains the Jenkins Configuration as Code (`casc.yaml`), required plugins list (`plugins.txt`), and Jenkins Shared Library for the Agentic PR Review platform.

## 1. Local Testing with Docker

To spin up a local Jenkins controller pre-configured with CasC and plugins:

```bash
docker compose up -d jenkins
```

Access Jenkins at `http://localhost:8080` (credentials: `admin` / `admin123!`).

## 2. Shared Library Setup

In Jenkins Global Pipeline Libraries:
- **Name**: `pr-review-lib`
- **Default version**: `main`
- **Retrieval method**: Modern SCM -> Git (`https://github.com/AniruddhaJoshi28/PR-reviewer.git`)
- **Library Path**: `jenkins/shared-library`

In your `Jenkinsfile`:
```groovy
@Library('pr-review-lib@main') _

pipeline {
    agent any
    stages {
        stage('Review') {
            steps {
                prReview(artifactsDir: 'artifacts', offline: true)
                publishResults('artifacts')
            }
        }
    }
}
```

## 3. Trusted vs Untrusted Execution Boundary

To prevent untrusted PR code from accessing Jenkins credentials or AI model tokens:
- **Untrusted Stages**: Checkout, unit testing, and test execution run in an ephemeral container with `--network=none` and without `withCredentials`.
- **Trusted Stages**: Risk classification, scanner verification, policy gates, and model dispatch run strictly on trusted agents.
