with open('gameplay/templates/gameplay/analytics.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# We just want one charts-grid and script.
# We will match from <div class="charts-grid"> to the end of the file.
text = re.sub(r'<div class="charts-grid">.*', '''<div class="charts-grid">
    <div class="chart-card">
        <div class="chart-title-sm">ACTIVITY OVER TIME</div>
        <div class="chart-title">12-Month Engagement Trend</div>
        <div style="height: 250px; background: #f8fafc; border-radius: 8px; display: flex; align-items: flex-end; padding: 10px; position:relative;">
            <canvas id="trendChart"></canvas>
        </div>
    </div>
    <div class="chart-card">
        <div class="chart-title-sm">CONTRIBUTION MIX</div>
        <div class="chart-title">Activity Breakdown</div>
        <div style="height: 250px; display: flex; align-items: center; justify-content: center; position:relative;">
           <canvas id="mixChart"></canvas>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<script>
    const labels = {{ chart_labels|safe }};
    const loginsData = {{ chart_logins|safe }};
    const problemsData = {{ chart_problems|safe }};
    const ideasData = {{ chart_ideas|safe }};

    const ctxTrend = document.getElementById('trendChart').getContext('2d');
    new Chart(ctxTrend, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Active Logins',
                    data: loginsData,
                    borderColor: '#1e5a40',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.1
                },
                {
                    label: 'Problems Raised',
                    data: problemsData,
                    borderColor: '#ca8a04',
                    borderWidth: 3,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.1
                },
                {
                    label: 'Trainings Created',
                    data: ideasData,
                    borderColor: '#0ea5e9',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    const ctxMix = document.getElementById('mixChart').getContext('2d');
    new Chart(ctxMix, {
        type: 'doughnut',
        data: {
            labels: ['Ideas', 'Problems', 'Training Enrolments'],
            datasets: [{
                data: [{{ mix_ideas_pct }}, {{ mix_probs_pct }}, {{ mix_trainings_pct }}],
                backgroundColor: ['#1e5a40', '#ca8a04', '#0ea5e9'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
</script>
{% endblock %}
''', text, flags=re.DOTALL)

with open('gameplay/templates/gameplay/analytics.html', 'w', encoding='utf-8') as f:
    f.write(text)