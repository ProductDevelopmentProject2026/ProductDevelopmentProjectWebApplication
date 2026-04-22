from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings              
from django.conf.urls.static import static
from gameplay.views import (
    dashboard, departments_page, ideas_page, vote_idea, 
    profile_page, training_page, register_training, add_question, 
    take_quiz, register_page, manage_lessons, view_lesson,
    department_detail, add_department_question, take_department_quiz, accept_idea,
    submit_feedback, problems_page, claim_solution, confirm_solved, reject_solution,
    redeem_page, company_admin_dashboard, edit_employee_profile, edit_department
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('company-admin/', company_admin_dashboard, name='company_admin_dashboard'),
    path('company-admin/edit-employee/<int:profile_id>/', edit_employee_profile, name='edit_employee_profile'),
    path('company-admin/edit-department/<int:dept_id>/', edit_department, name='edit_department'),
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
    path('signup/', register_page, name='signup'),
    path('redeem/', redeem_page, name='redeem_page'),
    path('training/<int:training_id>/lessons/', manage_lessons, name='manage_lessons'),
    path('lesson/<int:lesson_id>/', view_lesson, name='view_lesson'),
    path('department/<int:department_id>/', department_detail, name='department_detail'),
    path('department/<int:department_id>/add-quiz/', add_department_question, name='add_department_question'),
    path('department/<int:department_id>/take-quiz/', take_department_quiz, name='take_department_quiz'),
    path('idea/<int:idea_id>/accept/', accept_idea, name='accept_idea'),
    path('training/<int:training_id>/feedback/', submit_feedback, name='submit_feedback'),
    path('problems/', problems_page, name='problems_page'),
    path('problems/<int:problem_id>/claim/', claim_solution, name='claim_solution'),
    path('problems/<int:problem_id>/confirm/', confirm_solved, name='confirm_solved'),
    path('problems/<int:problem_id>/reject/', reject_solution, name='reject_solution'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)