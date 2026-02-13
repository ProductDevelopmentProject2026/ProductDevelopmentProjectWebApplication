from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from gameplay.views import dashboard, departments_page, ideas_page, vote_idea, profile_page
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),                 # Homepage
    path('departments/', departments_page, name='departments_page'), # New Page
    path('ideas/', ideas_page, name='ideas_page'),         # New Page
    path('vote/<int:idea_id>/', vote_idea, name='vote_idea'),
    path('profile/', profile_page, name='profile_page'),
    path('login/', auth_views.LoginView.as_view(template_name='gameplay/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]