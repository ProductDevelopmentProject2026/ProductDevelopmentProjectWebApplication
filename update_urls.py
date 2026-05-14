import os
import re

url_path = os.path.join('gameplay', 'urls.py')

with open(url_path, 'r', encoding='utf-8') as f:
    text = f.read()

if "name='stats_page'" not in text:
    text = re.sub(
        r'(urlpatterns\s*=\s*\[)',
        r"\1\n    path('stats/', views.stats_page, name='stats_page'),",
        text,
        count=1
    )
    with open(url_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully added stats_page to urls.py")
else:
    print("stats_page is already present in urls.py")