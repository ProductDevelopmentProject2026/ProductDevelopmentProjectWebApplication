from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings              
from django.conf.urls.static import static
from gameplay.views import (
    dashboard, departments_page, ideas_page, vote_idea, 
    profile_page, training_page, register_training, add_question, take_quiz, register_page
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),                 
    path('departments/', departments_page, name='departments_page'), 
    path('ideas/', ideas_page, name='ideas_page'),         
    path('vote/<int:idea_id>/', vote_idea, name='vote_idea'),
    path('profile/', profile_page, name='profile_page'),
    path('login/', auth_views.LoginView.as_view(template_name='gameplay/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('training/', training_page, name='training_page'),
    path('training/register/<int:training_id>/', register_training, name='register_training'),
    path('training/add-quiz/<int:training_id>/', add_question, name='add_question'),
    path('training/take-quiz/<int:training_id>/', take_quiz, name='take_quiz'),
    path('register/', register_page, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)