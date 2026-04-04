import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from gameplay.models import IdeaCategory

categories = [
    {"name": "Safety", "keywords": "safety, accident, hazard, ppe, health, danger, risk, fire, emergency, safe"},
    {"name": "Efficiency & Process", "keywords": "faster, time, speed, optimize, reduce, waste, process, tool, software, efficient"},
    {"name": "Facility & Welfare", "keywords": "break, cafeteria, cleaning, bathroom, parking, building, food, kitchen, desk, chair, workplace, office"},
    {"name": "IT & Software", "keywords": "computer, server, internet, wifi, bug, software, hardware, laptop, network, app"},
]

for cat_data in categories:
    IdeaCategory.objects.get_or_create(name=cat_data["name"], defaults={"keywords": cat_data["keywords"]})

print("Categories populated successfully.")
