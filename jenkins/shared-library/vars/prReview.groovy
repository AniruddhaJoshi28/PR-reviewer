def call(Map config = [:]) {
    def artifactsDir = config.get('artifactsDir', 'artifacts')
    def offline = config.get('offline', true)
    def aiProvider = config.get('aiProvider', 'offline')

    echo "Running PR review pipeline via Shared Library (artifacts: ${artifactsDir}, offline: ${offline})"
    sh """
        python -m pr_review.cli review --artifacts-dir ${artifactsDir} ${offline ? '--offline' : ''} --ai-provider ${aiProvider}
    """
}
