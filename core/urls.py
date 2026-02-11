from django.contrib import admin
from django.urls import path
from gameplay.views import dashboard  # Import your new view
from gameplay.views import dashboard, vote_idea

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),  # The empty '' means "Homepage"
    path('vote/<int:idea_id>/', vote_idea, name='vote_idea'),
]