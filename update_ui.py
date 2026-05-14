import re

with open('gameplay/templates/gameplay/base.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make navbar uppercase, update logo to black text, etc.
# Add ANALYTICS and ALERTS
nav_links_replacement = '''
        <div class="navbar-links">
            <a href="{% url 'dashboard' %}" class="navbar-brand" style="font-size: 1.5rem; font-weight: 800; color: #11201d; font-family: var(--font-serif); margin-right: 20px;">Prokevo</a>
            {% block nav_links %}
            <a href="{% url 'dashboard' %}">DASHBOARD</a>
            <a href="{% url 'departments_page' %}">DEPARTMENTS</a>
            <a href="{% url 'ideas_page' %}">IDEAS</a>
            <a href="{% url 'training_page' %}">TRAINING</a> 
            <a href="{% url 'problems_page' %}">PROBLEMS</a> 
            <a href="{% url 'redeem_page' %}">REWARDS</a>
            <a href="{% url 'analytics_page' %}" style="color: #1e5a40;">ANALYTICS</a>
            <a href="{% url 'profile_page' %}">MY STATS</a>
            
            {% if user.is_superuser %}
            <select id="tenantSwitcher" style="margin-left: 10px; margin-top: 0; margin-bottom: 0; padding: 4px 10px; border-radius: 6px; background: white; color: var(--text-primary); border: 1px solid var(--border-color); width: auto; font-size: 0.75rem;">
                <option value="">Default</option>
                {% for tenant in tenants %}
                    <option value="{{ tenant.subdomain }}" {% if active_tenant and active_tenant.id == tenant.id %}selected{% endif %}>{{ tenant.name }}</option>
                {% endfor %}
            </select>
            {% endif %}
            {% endblock nav_links %}
        </div>
        
        <div class="navbar-right" style="font-size: 0.8rem; font-weight: 700; display: flex; align-items: center; gap: 16px;">
        {% if user.is_authenticated %}
            {% if request.tenant and request.user.id == request.tenant.tenant_admin_id or request.user.is_superuser %}
                <a href="{% url 'company_admin_dashboard' %}" style="color: #4b5563; text-transform: uppercase;">⚙ ADMIN</a>
            {% endif %}
            <span style="cursor:pointer;">🌗</span>
            <a href="{% url 'alerts_page' %}" style="display:flex; align-items:center; gap: 6px; background: #eef2e6; color: #1e5a40; padding: 6px 12px; border-radius: 20px; font-weight: 700; text-transform: uppercase;">
                🔔 ALERTS <span style="background: #1e5a40; color: white; border-radius: 50%; width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.7rem;">1</span>
            </a>
            <a href="{% url 'profile_page' %}" style="color: #4b5563; text-transform: uppercase;">👤 PROFILE</a>
            <form action="{% url 'logout' %}" method="post" style="margin: 0;">
                {% csrf_token %}
                <button type="submit" style="background: white; border: 1px solid #d1d5db; color: #4b5563; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; cursor: pointer; padding: 6px 14px; border-radius: 6px;">LOGOUT</button>
            </form>
        {% else %}
            <a href="{% url 'login' %}" style="color: #4b5563; text-transform: uppercase; font-weight: 700; font-size: 0.8rem;">LOGIN</a>
            <a href="{% url 'signup' %}" style="background: #11201d; color: white; padding: 8px 16px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">SIGN UP</a>
        {% endif %}
        </div>
'''

text = re.sub(r'<div class="navbar-links">.*?</div>\s*<div class="navbar-right">.*?</div>', nav_links_replacement, text, flags=re.DOTALL)

with open('gameplay/templates/gameplay/base.html', 'w', encoding='utf-8') as f:
    f.write(text)