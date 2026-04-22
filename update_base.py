import os

base_template = """<!DOCTYPE html>
<html>
<head>
    <title>Employee Portal</title>
    <style>
        :root {
            /* Palette */
            --bg-color: #F7FAFC;
            --card-bg: #FFFFFF;
            --primary-action: #3182CE;
            --primary-hover: #2B6CB0;
            --text-primary: #1A202C;
            --text-secondary: #718096;
            --semantic-success: #48BB78;
            --semantic-danger: #F56565;
            --nav-bg: #1A202C;
            --border-color: #EDF2F7;
        }

        body { 
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color); 
            color: var(--text-primary);
            margin: 0; 
            padding: 0;
            line-height: 1.5;
        }
        
        /* Navigation Bar Styles */
        .navbar { 
            background: var(--nav-bg); 
            padding: 16px 32px; 
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .navbar-links {
            display: flex;
            gap: 24px;
            align-items: center;
        }
        .navbar a { 
            color: #E2E8F0; 
            text-decoration: none; 
            font-weight: 500; 
            font-size: 1rem; 
            transition: color 0.2s;
        }
        .navbar a:hover { color: var(--primary-action); }
        
        .navbar-right {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .btn-primary {
            background-color: var(--primary-action);
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s;
            text-decoration: none;
            display: inline-block;
        }
        .btn-primary:hover {
            background-color: var(--primary-hover);
            color: white;
        }

        /* Card Styles */
        .card { 
            background: var(--card-bg); 
            padding: 24px; 
            margin-bottom: 24px; 
            border-radius: 4px; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); 
            border: none;
        }
        
        /* Form & Content Constraints */
        .form-container, .content-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }

        input[type=text], input[type=number], input[type=email], input[type=password], textarea, select { 
            width: 100%; 
            padding: 10px 12px; 
            border: 1px solid var(--border-color); 
            border-radius: 4px; 
            box-sizing: border-box; 
            font-family: inherit;
            color: var(--text-primary);
            margin-top: 8px;
            margin-bottom: 16px;
            transition: border-color 0.2s;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--primary-action);
            box-shadow: 0 0 0 1px var(--primary-action);
        }

        h1, h2, h3, h4 { color: var(--text-primary); margin-top: 0; }
        p { color: var(--text-secondary); }
        
        .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
        .text-success { color: var(--semantic-success); font-weight: 600; }
        .text-danger { color: var(--semantic-danger); font-weight: 600; }

        .gamification-score {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--primary-action);
            line-height: 1;
        }
        
        .list-item {
            padding: 16px 0;
            border-bottom: 1px solid var(--border-color);
        }
        .list-item:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="navbar-links">
            <a href="{% url 'dashboard' %}" style="font-weight: 700; color: white; margin-right: 12px; font-size: 1.2rem;">Portal</a>
            <a href="{% url 'dashboard' %}">Home</a>
            <a href="{% url 'departments_page' %}">Departments</a>
            <a href="{% url 'ideas_page' %}">Ideas</a>
            <a href="{% url 'training_page' %}">Training</a> 
            <a href="{% url 'problems_page' %}">Problems</a> 
            <a href="{% url 'redeem_page' %}">Rewards</a>
            
            {% if user.is_superuser %}
            <select id="tenantSwitcher" style="margin-left: 20px; margin-top: 0; margin-bottom: 0; padding: 6px 12px; border-radius: 4px; background: #2D3748; color: white; border: 1px solid #4A5568; width: auto;">
                <option value="">-- Select Org --</option>
                {% for tenant in tenants %}
                    <option value="{{ tenant.subdomain }}" {% if active_tenant and active_tenant.id == tenant.id %}selected{% endif %}>{{ tenant.name }}</option>
                {% endfor %}
            </select>
            {% endif %}
        </div>
        
        <div class="navbar-right">
        {% if user.is_authenticated %}
            {% if request.tenant and request.user.id == request.tenant.tenant_admin_id or request.user.is_superuser %}
                <a href="{% url 'company_admin_dashboard' %}" style="color: #F6AD55;">⚙️ Admin</a>
            {% endif %}
            <a href="{% url 'profile_page' %}">👤 Profile</a>
            <form action="{% url 'logout' %}" method="post" style="margin: 0; display: inline;">
                {% csrf_token %}
                <button type="submit" style="background: none; border: none; color: #E2E8F0; font-weight: 500; font-size: 1rem; cursor: pointer; padding: 0;">Logout</button>
            </form>
        {% else %}
            <a href="{% url 'login' %}">Login</a>
            <a class="btn-primary" href="{% url 'signup' %}">Sign Up</a>
        {% endif %}
        </div>
    </nav>
    <div class="content-container">
        {% block content %}
        {% endblock %}
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            const switcher = document.getElementById('tenantSwitcher');
            if (!switcher) return;

            // Handle user switching tenant manually
            switcher.addEventListener('change', function(e) {
                const url = new URL(window.location.href);
                url.searchParams.set('tenant', e.target.value);
                window.location.href = url.toString();
            });
        });

        // Intercept native fetch API to append headers
        const originalFetch = window.fetch;
        window.fetch = async function() {
            let [resource, config] = arguments;
            const activeTenantId = "{{ active_tenant.id|default:'' }}";
            
            if (activeTenantId) {
                if (!config) config = {};
                if (!config.headers) config.headers = {};
                
                // Only inject if it's an object (handles Headers object wrapping if needed)
                if (config.headers instanceof Headers) config.headers.append('X-Tenant-Id', activeTenantId);
                else config.headers['X-Tenant-Id'] = activeTenantId;
            }
            return await originalFetch(resource, config);
        };
    </script>
</body>
</html>
"""

filepath = os.path.join("gameplay", "templates", "gameplay", "base.html")
with open(filepath, "w", encoding="utf-8") as f:
    f.write(base_template)
print("Updated successfully")
