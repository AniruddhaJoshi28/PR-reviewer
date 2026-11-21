def call(Map config = [:]) {
    def offline = config.get('offline', false)
    echo "Executing security scanners (real=${!offline}, mock=${offline})"
    sh """
        python -m pr_review.cli scan ${offline ? '--offline' : '--real'}
    """
}
