import re

with open('gameplay/templates/gameplay/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure it replaced correctly
if '{% for log in action_logs %}' not in text:
    replacement = '''
<div class="alerts-header">
    <div>
        <p>NOTIFICATIONS</p>
        <h1>What changed today</h1>
        <div class="alerts-subtitle">A clean feed of the ideas, trainings, problems, and progress updates that matter inside your company.</div>
    </div>
    <div class="alerts-actions">
        <span class="unread-pill">{{ action_logs|length }} NOTIFICATIONS</span>
        <a href="{% url 'dashboard' %}" class="btn-read" style="text-decoration: none;">Back to Dashboard</a>
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
{% endblock %}
'''
    text = re.sub(r'<div class="alerts-header">.*', replacement, text, flags=re.DOTALL)
    with open('gameplay/templates/gameplay/alerts.html', 'w', encoding='utf-8') as f:
        f.write(text)