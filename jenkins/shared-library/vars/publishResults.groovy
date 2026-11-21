def call(String artifactsDir = 'artifacts') {
    echo "Archiving PR review artifacts from: ${artifactsDir}"
    archiveArtifacts artifacts: "${artifactsDir}/**", fingerprint: true, allowEmptyArchive: false
    junit testResults: "${artifactsDir}/*.xml", allowEmptyResults: true
}
