(() => {
    const categories = [
        "Doctor Consultation",
        "Nursing Care",
        "Cleanliness & Hygiene",
        "Hospital Facilities",
        "Emergency Services",
        "Pharmacy Service",
        "Waiting Time",
        "Staff Behaviour"
    ];
    let ratingsChart = null;
    let sentimentChart = null;

    window.addEventListener("careline:feedback-loaded", event => {
        const errorMessage = document.getElementById("analyticsError");
        if (typeof Chart === "undefined") {
            errorMessage.textContent =
                "Charts are unavailable. Check your internet connection and reload.";
            errorMessage.style.display = "block";
            return;
        }
        errorMessage.textContent = "";
        errorMessage.style.display = "none";

        if (ratingsChart) ratingsChart.destroy();
        if (sentimentChart) sentimentChart.destroy();

        const feedback = event.detail;
        const averageRatings = categories.map(category => {
            const values = feedback
                .map(record => Number((record.ratings || {})[category]))
                .filter(value => Number.isFinite(value) && value >= 1 && value <= 5);
            return values.length
                ? Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2))
                : 0;
        });

        ratingsChart = new Chart(document.getElementById("ratingsChart"), {
            type: "bar",
            data: {
                labels: categories,
                datasets: [{
                    label: "Average rating (out of 5)",
                    data: averageRatings,
                    backgroundColor: "#176b87",
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {beginAtZero: true, max: 5, ticks: {stepSize: 1}}
                },
                plugins: {legend: {display: false}}
            }
        });

        const sentimentLabels = ["Positive", "Neutral", "Negative"];
        const sentimentCounts = sentimentLabels.map(label =>
            feedback.filter(record => record.sentiment === label).length
        );

        sentimentChart = new Chart(document.getElementById("sentimentChart"), {
            type: "doughnut",
            data: {
                labels: sentimentLabels,
                datasets: [{
                    data: sentimentCounts,
                    backgroundColor: ["#3c9b68", "#c9a45c", "#c85445"],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {legend: {position: "bottom"}}
            }
        });
    });
})();
