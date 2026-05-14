import re

# Update analytics.html
with open('gameplay/templates/gameplay/analytics.html', 'r', encoding='utf-8') as f:
    text = f.read()

replacements_analytics = {
    '<div class="stat-value">6</div>': '<div class="stat-value">{{ ideas_submitted }}</div>',
    '<div class="stat-sub">3 accepted</div>': '<div class="stat-sub">{{ ideas_accepted }} accepted</div>',
    '<div class="stat-pill">50% acceptance</div>': '<div class="stat-pill">{{ acceptance_rate }}% acceptance</div>',
    '<div class="stat-value">5</div>\\s*<div class="stat-label">PROBLEMS RAISED</div>': '<div class="stat-value">{{ problems_raised }}</div>\\n        <div class="stat-label">PROBLEMS RAISED</div>',
    '<div class="stat-sub">3 resolved</div>': '<div class="stat-sub">{{ problems_resolved }} resolved</div>',
    '<div class="stat-pill">60% resolved</div>': '<div class="stat-pill">{{ resolved_rate }}% resolved</div>',
    '<div class="stat-value">18</div>': '<div class="stat-value">{{ team_members }}</div>',
    '<div class="stat-sub">6 active this month</div>': '<div class="stat-sub">{{ active_this_month }} active this month</div>',
    '<div class="stat-pill" style="color: #c2410c; background: #ffedd5; border-color: #fed7aa;">33% engaged</div>': '<div class="stat-pill" style="color: #c2410c; background: #ffedd5; border-color: #fed7aa;">{{ engagement_rate }}% engaged</div>',
    '<div class="stat-value">143</div>': '<div class="stat-value">{{ total_points }}</div>',
    '<div class="stat-sub">€180 in bonuses</div>': '<div class="stat-sub">€{{ total_bonuses }} in bonuses</div>',
    '<div class="stat-pill">24 quiz completions</div>': '<div class="stat-pill">{{ quizzes_completed }} quiz completions</div>',
    '<div class="stat-value">5</div>\\s*<div class="stat-label">TRAININGS CREATED</div>': '<div class="stat-value">{{ trainings_created }}</div>\\n        <div class="stat-label">TRAININGS CREATED</div>',
    '<div class="stat-value">10</div>\\s*<div class="stat-label">TRAINING ENROLMENTS</div>': '<div class="stat-value">{{ training_enrollments }}</div>\\n        <div class="stat-label">TRAINING ENROLMENTS</div>',
    '<div class="stat-value">4</div>\\s*<div class="stat-label">ACTIVE LAST 7 DAYS</div>': '<div class="stat-value">{{ active_last_7_days }}</div>\\n        <div class="stat-label">ACTIVE LAST 7 DAYS</div>',
    '<div class="stat-value">24</div>\\s*<div class="stat-label">QUIZZES COMPLETED</div>': '<div class="stat-value">{{ quizzes_completed }}</div>\\n        <div class="stat-label">QUIZZES COMPLETED</div>'
}

for k, v in replacements_analytics.items():
    text = re.sub(k, v, text)

with open('gameplay/templates/gameplay/analytics.html', 'w', encoding='utf-8') as f:
    f.write(text)

# Update alerts.html
with open('gameplay/templates/gameplay/alerts.html', 'r', encoding='utf-8') as f:
    alerts_text = f.read()

alerts_replacement = '''
<div class="alerts-header">
    <div>
        <p>NOTIFICATIONS</p>
        <h1>What changed today</h1>
        <div class="alerts-subtitle">A clean feed of the ideas, trainings, problems, and progress updates that matter inside your company.</div>
    </div>
    <div class="alerts-actions">
        <span class="unread-pill">{{ action_logs|length }} NOTIFICATIONS</span>
        <a href="{% url 'dashboard' %}" class="btn-read">Back to Dashboard</a>
    </div>
</div>

{% for log in action_logs %}
<div class="alert-card">
    <div class="icon-wrapper">⭐</div>
    <div class="alert-content">
        <div class="alert-title">{{ log.action_name }}</div>
        <div class="alert-desc">User {{ log.user.username }} earned +{{ log.points }} points.</div>
        <div class="alert-meta">{{ log.date_created|timesince }} AGO &nbsp;&nbsp; BY {{ log.user.username|upper }}</div>
    </div>
    <div class="alert-card-actions">
        <div class="dot"></div>
    </div>
</div>
{% empty %}
<div class="alert-card" style="justify-content: center; padding: 40px; color: var(--text-secondary);">
    No recent activity found.
</div>
{% endfor %}
'''

alerts_text = re.sub(
    r'<div class="alerts-header">.*</div>\s*<div class="alert-card">.*?</div>\s*</div>',
    alerts_replacement.strip(),
    alerts_text,
    flags=re.DOTALL
)

with open('gameplay/templates/gameplay/alerts.html', 'w', encoding='utf-8') as f:
    f.write(alerts_text)