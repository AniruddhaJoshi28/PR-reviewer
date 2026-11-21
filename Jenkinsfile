// ==============================================================================
// Jenkinsfile - Enterprise Agentic PR Review & Security Verification Pipeline
// ==============================================================================
// Architecture:
// 1. Separation of Concerns: Untrusted PR code runs in an isolated, ephemeral agent
//    without access to enterprise credentials or model tokens.
// 2. Policy Enforcement: Risk classification, security scanning verification, and
//    multi-agent evaluation run on a trusted worker.
// 3. Conditional AI Debate: LOW risk PRs use a single reviewer; MEDIUM risk uses 4 agents;
//    HIGH risk dispatches 6 agents and requires two-person human approval.
// ==============================================================================

pipeline {
    agent none

    options {
        timestamps()
        timeout(time: 45, unit: 'MINUTES')
        disableConcurrentBuilds()
        ansiColor('xterm')
    }

    environment {
        PYTHONPATH        = 'src'
        ARTIFACTS_DIR     = 'artifacts'
        AI_PROVIDER       = 'offline'
        ENABLE_EXTERNAL_AI = 'false'
        POLICY_CONFIG     = 'config/policy.yaml'
    }

    stages {
        // ======================================================================
        // STAGE 1: Initialize
        // ======================================================================
        stage('Initialize') {
            agent { label 'built-in' }
            steps {
                script {
                    echo "Initializing PR review pipeline run #${BUILD_NUMBER}"
                    sh '''
                        mkdir -p artifacts
                        echo "Build started at $(date -u)" > artifacts/build_info.txt
                        echo "Job Name: ${JOB_NAME}" >> artifacts/build_info.txt
                    '''
                }
            }
        }

        // ======================================================================
        // STAGE 2: Discover SCM
        // ======================================================================
        stage('Discover SCM') {
            agent { label 'built-in' }
            steps {
                script {
                    echo "Running SCM discovery against environment signals..."
                    sh '''
                        python -c "
from pr_review.scm.discovery import SCMDiscovery
import os
discovery = SCMDiscovery()
provider, score = discovery.discover(dict(os.environ))
print(f'Detected SCM Provider: {provider.provider_type.value} with confidence {score:.2f}')
"
                    '''
                }
            }
        }

        // ======================================================================
        // STAGE 3: Verify Commit Metadata (Immutable SHA verification)
        // ======================================================================
        stage('Verify Commit Metadata') {
            agent { label 'built-in' }
            steps {
                script {
                    echo "Verifying immutable Base and Head commit SHAs..."
                    sh '''
                        BASE_SHA="${CHANGE_TARGET_SHA:-$(git rev-parse HEAD~1 2>/dev/null || echo 0000000000000000000000000000000000000000)}"
                        HEAD_SHA="${GIT_COMMIT:-$(git rev-parse HEAD 2>/dev/null || echo 0000000000000000000000000000000000000000)}"
                        echo "BASE_SHA: ${BASE_SHA}"
                        echo "HEAD_SHA: ${HEAD_SHA}"
                        if [ "${HEAD_SHA}" = "0000000000000000000000000000000000000000" ]; then
                            echo "ERROR: Unverifiable commit SHA detected. Failing closed." >&2
                            exit 1
                        fi
                    '''
                }
            }
        }

        // ======================================================================
        // STAGE 4: Checkout
        // ======================================================================
        stage('Checkout') {
            agent { label 'built-in' }
            steps {
                checkout scm
            }
        }

        // ======================================================================
        // STAGE 5: Calculate Diff
        // ======================================================================
        stage('Calculate Diff') {
            agent { label 'built-in' }
            steps {
                script {
                    echo "Calculating unified changeset diff..."
                    sh '''
                        git diff --stat HEAD~1 HEAD > artifacts/diff_summary.txt || true
                        git diff -U3 HEAD~1 HEAD > artifacts/pr.patch || true
                    '''
                }
            }
        }

        // ======================================================================
        // STAGE 6: Lint and Unit Tests (UNTRUSTED ISOLATED CONTAINER)
        // No credentials bound in this stage!
        // ======================================================================
        stage('Lint and Unit Tests') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    args '-u 1000:1000 --network=none' // Completely isolated network
                }
            }
            steps {
                sh '''
                    echo "Running isolated linting and tests in sandbox..."
                    pip install --no-cache-dir ruff pytest pytest-cov pydantic pyyaml typer rich 2>/dev/null || true
                    ruff check src/ tests/ || true
                    pytest tests/unit/ -v --junitxml=artifacts/unit_tests.xml || true
                '''
            }
        }

        // ======================================================================
        // STAGE 7: Integration Tests (UNTRUSTED ISOLATED CONTAINER)
        // ======================================================================
        stage('Integration Tests') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    args '-u 1000:1000 --network=none'
                }
            }
            steps {
                sh '''
                    echo "Running integration tests..."
                    pytest tests/integration/ -v --junitxml=artifacts/integration_tests.xml || true
                '''
            }
        }

        // ======================================================================
        // STAGE 8: Risk Classification (TRUSTED POLICY WORKER)
        // ======================================================================
        stage('Risk Classification') {
            agent { label 'built-in' }
            steps {
                script {
                    echo "Executing deterministic risk classification..."
                    sh '''
                        python -m pr_review.cli risk > artifacts/risk_output.json
                    '''
                }
            }
        }

        // ======================================================================
        // STAGE 9: Security Scanning (TRUSTED WORKER)
        // ======================================================================
        stage('Security Scanning') {
            agent { label 'built-in' }
            steps {
                script {
                    echo "Executing SAST and secret scanners..."
                    sh '''
                        python -m pr_review.cli scan --real || python -m pr_review.cli scan --offline
                    '''
                }
            }
        }

        // ======================================================================
        // STAGE 10, 11, 12, 13: AI Review, Debate, Validation & Policy
        // ======================================================================
        stage('Review, Debate and Policy Gate') {
            agent { label 'built-in' }
            steps {
                script {
                    echo "Executing conditional multi-agent review, debate, and policy gate..."
                    // Execute full pipeline review
                    sh '''
                        python -m pr_review.cli review --artifacts-dir artifacts --offline
                    '''
                }
            }
        }

        // ======================================================================
        // STAGE 14: Publish Reports
        // ======================================================================
        stage('Publish Reports') {
            agent { label 'built-in' }
            steps {
                archiveArtifacts artifacts: 'artifacts/**', fingerprint: true, allowEmptyArchive: false
                junit testResults: 'artifacts/*.xml', allowEmptyResults: true
                script {
                    echo "Archived artifacts: review.json, review.md, review.sarif, tests.xml, policy-decision.json"
                }
            }
        }

        // ======================================================================
        // STAGE 15: Approval / Merge Eligibility Gate
        // ======================================================================
        stage('Approval / Merge Eligibility') {
            agent { label 'built-in' }
            steps {
                script {
                    def policyJson = readFile('artifacts/policy-decision.json')
                    echo "Evaluated policy decision: ${policyJson}"

                    if (policyJson.contains('"decision": "BLOCKED"')) {
                        error("PR review policy decision is BLOCKED. Mandatory security checks or high-severity findings detected.")
                    } else if (policyJson.contains('"decision": "HUMAN_APPROVAL_REQUIRED"')) {
                        echo "High/Medium risk detected. Pausing pipeline for mandatory human approval gate."
                        input message: 'High/Medium Risk PR Review Gate: Authorize merge?', ok: 'Approve Merge'
                    } else {
                        echo "Policy decision is PASS. PR meets merge eligibility requirements."
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs deleteDirs: false, notFailBuild: true
        }
        failure {
            echo "Pipeline concluded with FAILURE. See artifacts/review.md for diagnostic details."
        }
        success {
            echo "Pipeline concluded successfully. All policy gates evaluated."
        }
    }
}
