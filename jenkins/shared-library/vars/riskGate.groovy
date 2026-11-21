def call(String riskLevel, Closure body) {
    echo "Evaluating risk gate for level: ${riskLevel}"
    if (riskLevel == 'HIGH' || riskLevel == 'MEDIUM') {
        body()
    } else {
        echo "Risk level is LOW. Skipping advanced multi-agent debate stage."
    }
}
