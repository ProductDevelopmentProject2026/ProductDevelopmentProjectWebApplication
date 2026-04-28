from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum, Avg, Q
from .models import Department, Idea, IdeaCategory, Profile, Training, Question, QuizResult, Lesson, TrainingFeedback, Problem, Invite, Tenant
from .forms import IdeaForm, TrainingForm, QuestionForm, LessonForm, UserRegisterForm, ProblemForm, SolutionForm, EmployeeEditForm, DepartmentForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
import re  
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from .thread_local import set_current_tenant
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.core.mail import send_mail
import csv
import io
import uuid
import logging

logger = logging.getLogger(__name__)

# 0. Company Admin Dashboard
@login_required
def company_admin_dashboard(request):
    if not request.tenant:
        messages.info(request, "Please select an organization to view the admin panel.")
        return redirect('dashboard')
        
    # Check if the user is the assigned admin for the tenant or a master admin
    is_tenant_admin = getattr(request.tenant, 'tenant_admin_id', None) == request.user.id
    if not request.user.is_superuser and not is_tenant_admin:
        messages.error(request, "You do not have permission to access the Company Admin dashboard.")
        return redirect('dashboard')
        
    departments = Department.objects.filter(tenant=request.tenant).annotate(
        points=Sum('profile__total_score')
    ).order_by('-points')
    
    users = Profile.objects.filter(tenant=request.tenant).select_related('user', 'department')
    trainings = Training.objects.filter(tenant=request.tenant)
    
    return render(request, 'gameplay/company_admin_dashboard.html', {
        'tenant': request.tenant,
        'departments': departments,
        'users': users,
        'trainings': trainings,
    })

@login_required
def edit_employee_profile(request, profile_id):
    if not request.tenant:
        messages.info(request, "Please select an organization.")
        return redirect('dashboard')
    
    is_tenant_admin = getattr(request.tenant, 'tenant_admin_id', None) == request.user.id
    if not request.user.is_superuser and not is_tenant_admin:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')

    employee_profile = get_object_or_404(Profile, id=profile_id, tenant=request.tenant)
    employee_user = employee_profile.user

    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, instance=employee_user, tenant=request.tenant, profile=employee_profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully updated profile for {employee_user.username}.")
            return redirect('company_admin_dashboard')
    else:
        form = EmployeeEditForm(instance=employee_user, tenant=request.tenant, profile=employee_profile)

    return render(request, 'gameplay/edit_employee_profile.html', {
        'form': form,
        'employee_profile': employee_profile,
        'tenant': request.tenant,
    })

@login_required
def edit_department(request, dept_id):
    if not request.tenant:
        messages.info(request, "Please select an organization.")
        return redirect('dashboard')
    
    is_tenant_admin = getattr(request.tenant, 'tenant_admin_id', None) == request.user.id
    if not request.user.is_superuser and not is_tenant_admin:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')

    department = get_object_or_404(Department, id=dept_id, tenant=request.tenant)

    if request.method == 'POST':
        form = DepartmentForm(request.POST, request.FILES, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully updated department {department.name}.")
            return redirect('company_admin_dashboard')
    else:
        form = DepartmentForm(instance=department)

    return render(request, 'gameplay/edit_department.html', {
        'form': form,
        'department': department,
        'tenant': request.tenant,
    })

@login_required
def edit_company(request):
    if not request.tenant:
        messages.error(request, "Please select an organization first.")
        return redirect('dashboard')
        
    is_tenant_admin = getattr(request.tenant, 'tenant_admin_id', None) == request.user.id
    if not request.user.is_superuser and not is_tenant_admin:
        messages.error(request, "You do not have permission.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            request.tenant.name = name
            request.tenant.save()
            messages.success(request, "Company details updated successfully.")
            return redirect('company_admin_dashboard')
            
    return render(request, 'gameplay/edit_company.html', {'tenant': request.tenant})

@login_required
def edit_company_user(request, user_id):
    if not request.tenant:
        return redirect('dashboard')
        
    is_tenant_admin = getattr(request.tenant, 'tenant_admin_id', None) == request.user.id
    if not request.user.is_superuser and not is_tenant_admin:
        messages.error(request, "You do not have permission.")
        return redirect('dashboard')
        
    profile = get_object_or_404(Profile, user__id=user_id, tenant=request.tenant)
    departments = Department.objects.filter(tenant=request.tenant)
    
    if request.method == 'POST':
        dept_id = request.POST.get('department')
        profile.department_id = dept_id if dept_id else None
        profile.total_score = int(request.POST.get('points', profile.total_score))
        profile.save()
        messages.success(request, f"User {profile.user.username} updated successfully.")
        return redirect('company_admin_dashboard')
        
    return render(request, 'gameplay/edit_company_user.html', {'profile': profile, 'departments': departments})

# 1. Home Page (Welcome)
@login_required
def dashboard(request):
    if not request.tenant:
        messages.info(request, "Please select an organization from the dropdown above to view the dashboard.")
        departments = Department.objects.none()
    else:
        departments = Department.objects.filter(tenant=request.tenant).annotate(
            points=Sum('profile__total_score')
        ).order_by('-points')

    dept_data = []
    for dept in departments:
        total = dept.points or 0
        dept_data.append({
            'dept': dept,
            'total_points': total,
        })

    max_points = max((d['total_points'] for d in dept_data), default=1)
    if max_points == 0:
        max_points = 1

    MIN_HEIGHT = 30
    MAX_HEIGHT = 120  # reduced so buildings stay on the grid

    # Color palette for accent (used on the top department)
    colors = ['#06b6d4', '#f43f5e', '#f97316', '#22c55e', '#ef4444', '#64748b',
              '#8b5cf6', '#ec4899', '#14b8a6', '#eab308']

    # Grid positions — spread buildings nicely within the grid
    positions = [
        (15, 30), (15, 60),
        (38, 15), (38, 45), (38, 72),
        (62, 25), (62, 55),
        (80, 15), (80, 45), (80, 72),
    ]

    for i, d in enumerate(dept_data):
        ratio = (d['total_points'] / max_points) ** 0.5
        
        d['dept'].building_height = int(MIN_HEIGHT + ratio * (MAX_HEIGHT - MIN_HEIGHT))
        d['dept'].total_points_display = d['total_points']
        d['dept'].color = colors[i % len(colors)]
        pos = positions[i % len(positions)]
        d['dept'].pos_top = pos[0]
        d['dept'].pos_left = pos[1]
        # Mark the top department so the template can highlight it
        d['dept'].is_top = (i == 0 and d['total_points'] > 0)

    return render(request, 'gameplay/dashboard.html', {
        'departments': [d['dept'] for d in dept_data],
    })

# 2. Departments Page
def departments_page(request):
    if not request.tenant:
        messages.info(request, "Please select an organization to view departments.")
        all_departments = Department.objects.none()
    else:
        all_departments = Department.objects.filter(tenant=request.tenant).annotate(
            total_points=Sum('profile__total_score')
        ).order_by('-total_points')
    
    return render(request, 'gameplay/departments.html', {'departments': all_departments})

# 3. Ideas Page (Form + List)
def ideas_page(request):
    if request.method == 'POST':
        if not request.tenant:
            messages.error(request, "You must select an organization first.")
            return redirect('ideas_page')
            
        form = IdeaForm(request.POST)
        if form.is_valid():
            new_idea = form.save(commit=False)
            new_idea.submitted_by = request.user
            new_idea.tenant = request.tenant
            
            # Auto-categorization logic
            text_to_search = (new_idea.title + " " + new_idea.description).lower()
            categories = IdeaCategory.objects.filter(tenant=request.tenant)
            for cat in categories:
                kws = [k.strip().lower() for k in cat.keywords.split(',')]
                if any(kw in text_to_search for kw in kws if kw):
                    new_idea.category = cat
                    break
                    
            new_idea.save()
            return redirect('ideas_page') 
    else:
        form = IdeaForm()

    search_query = request.GET.get('q', '')

    if not request.tenant:
        messages.info(request, "Please select an organization to view ideas.")
        pending_ideas = Idea.objects.none()
    else:
        if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.department:
            user_dept = request.user.profile.department
            pending_ideas = Idea.objects.filter(tenant=request.tenant).exclude(accepted_by=user_dept)
        else:
            pending_ideas = Idea.objects.filter(tenant=request.tenant)

    if search_query:
        pending_ideas = pending_ideas.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    pending_ideas = pending_ideas.annotate(num_votes=Count('voters')).order_by('title')

    if not request.tenant:
        categories = IdeaCategory.objects.none()
    else:
        categories = IdeaCategory.objects.filter(tenant=request.tenant)
        
    categorized_ideas = []
    
    for cat in categories:
        cat_ideas = pending_ideas.filter(category=cat)
        if cat_ideas.exists() or search_query:  # show category if exists or if searching
            categorized_ideas.append({
                'category': cat,
                'ideas': cat_ideas
            })
            
    uncategorized = pending_ideas.filter(category__isnull=True)
    if uncategorized.exists() or search_query:
        # We can simulate a category object via dictionary for the template
        class DummyCategory:
            name = "General / Other"
        categorized_ideas.append({
            'category': DummyCategory(),
            'ideas': uncategorized
        })

    return render(request, 'gameplay/ideas.html', {
        'categorized_ideas': categorized_ideas, 
        'form': form,
        'search_query': search_query
    })

# 4. Voting Logic
def vote_idea(request, idea_id):
    idea = get_object_or_404(Idea, pk=idea_id, tenant=request.tenant)
    if request.user.is_authenticated:
        if request.user in idea.voters.all():
            idea.voters.remove(request.user)
        else:
            idea.voters.add(request.user)
    return redirect('ideas_page') # Go back to ideas page

@login_required
def profile_page(request):
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        # Fallback to create the profile if it somehow doesn't exist
        user_profile = Profile.objects.create(user=request.user)

    if not request.tenant:
        messages.info(request, "Please select an organization to view your profile data.")
        my_ideas = Idea.objects.none()
        my_trainings = Training.objects.none()
    else:
        my_ideas = Idea.objects.filter(submitted_by=request.user, tenant=request.tenant).order_by('title')
        my_trainings = Training.objects.filter(organizer=request.user, tenant=request.tenant).order_by('title')
        
    accepted_ideas_count = my_ideas.filter(accepted_by__isnull=False).distinct().count()
    pending_ideas_count = my_ideas.filter(accepted_by__isnull=True).count()

    # --- NEW: Training Analytics Logic ---
    training_stats = []

    for t in my_trainings:
        registered = t.attendees.count()
        # Count how many unique users actually finished the quiz
        finished = QuizResult.objects.filter(training=t).values('user').distinct().count()
        
        feedbacks = t.feedbacks.all().order_by('-created_at')
        avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0

        training_stats.append({
            'training': t,
            'registered_count': registered,
            'finished_count': finished,
            'avg_rating': round(avg_rating, 1), # Round to 1 decimal place (e.g., 4.5)
            'feedbacks': feedbacks
        })
        
    # Get redeemed rewards
    from .models import RedeemedReward
    redeemed_rewards = RedeemedReward.objects.filter(user=request.user).order_by('-date_redeemed')

    return render(request, 'gameplay/profile.html', {
        'profile': user_profile,
        'my_ideas': my_ideas,
        'accepted_ideas_count': accepted_ideas_count,
        'pending_ideas_count': pending_ideas_count,
        'training_stats': training_stats, # Pass stats to the template
        'redeemed_rewards': redeemed_rewards,
    })

# 5. Training Page (List + Create)
def training_page(request):
    if request.method == 'POST':
        if not request.tenant:
            messages.error(request, "You must select an organization first.")
            return redirect('training_page')
            
        form = TrainingForm(request.POST, request.FILES)
        if form.is_valid():
            new_training = form.save(commit=False)
            new_training.organizer = request.user
            new_training.tenant = request.tenant
            new_training.save()
            
            from django.contrib import messages
            messages.success(request, "Training created! You earned a 50€ bonus.")
            
            return redirect('training_page')
    else:
        form = TrainingForm()

    search_query = request.GET.get('q', '')

    if not request.tenant:
        messages.info(request, "Please select an organization to view trainings.")
        trainings = Training.objects.none()
    else:
        trainings = Training.objects.filter(tenant=request.tenant)

    if search_query:
        trainings = trainings.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Get all trainings, sorted by the first letter (title)
    trainings = trainings.order_by('title')

    return render(request, 'gameplay/training.html', {
        'trainings': trainings, 
        'form': form,
        'search_query': search_query
    })

# 6. Registration Logic (Like Voting), (Updated with Department Block)
def register_training(request, training_id):
    training = get_object_or_404(Training, pk=training_id, tenant=request.tenant)

    if request.user.is_authenticated:
        
        # --- NEW: Check if the user is the organizer ---
        if request.user == training.organizer:
            messages.error(request, "You cannot register for a training that you created.")
            return redirect('training_page')
        # -----------------------------------------------

        # Normal Registration / Un-registration
        if request.user in training.attendees.all():
            training.attendees.remove(request.user) 
            messages.success(request, "You have left the training.")
        else:
            training.attendees.add(request.user)    
            messages.success(request, "Successfully registered for the training!")

    return redirect('training_page')

# 7. Organizer adds a question
def add_question(request, training_id):
    training = get_object_or_404(Training, pk=training_id, tenant=request.tenant)
    
    # Security: Only the organizer can add questions
    if request.user != training.organizer:
        return redirect('training_page')

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.training = training
            question.tenant = request.tenant
            question.save()
            return redirect('add_question', training_id=training.id) # Reload to add another
    else:
        form = QuestionForm()

    # Show list of existing questions below the form
    existing_questions = training.questions.all()
    
    return render(request, 'gameplay/add_question.html', {
        'training': training, 
        'form': form, 
        'questions': existing_questions
    })

# 8. Attendees take the quiz
def take_quiz(request, training_id):
    training = get_object_or_404(Training, pk=training_id, tenant=request.tenant)
    questions = training.questions.all()

    if request.method == 'POST':
        score = 0
        feedback = []

        for q in questions:
            selected_option = request.POST.get(f'question_{q.id}')
            is_correct = (selected_option == q.correct_option)
            
            if is_correct:
                score += 1
            
            # Save the details of this specific question to show the user later
            feedback.append({
                'question_obj': q,
                'selected': selected_option,
                'correct_answer': q.correct_option,
                'is_correct': is_correct
            })

        attendee_dept = request.user.profile.department
        organizer_dept = training.organizer.profile.department

        if attendee_dept != organizer_dept:
            already_rewarded = QuizResult.objects.filter(
                training=training
            ).exclude(user__profile__department=organizer_dept).exists()

            if not already_rewarded:
                training.organizer.profile.bonus_euros += 50
                training.organizer.profile.save()

        # Save result and give points
        QuizResult.objects.create(training=training, user=request.user, score=score, tenant=request.tenant)
        request.user.profile.total_score += (score * 10)
        request.user.profile.save()

        return render(request, 'gameplay/quiz_results.html', {
            'training': training,
            'score': score,
            'total_questions': questions.count(),
            'feedback': feedback
        })

    return render(request, 'gameplay/take_quiz.html', {'training': training, 'questions': questions})

# 9. Registration Page
def register_page(request):
    token = request.GET.get('token') or request.POST.get('token') or request.session.get('invite_token')

    try:
        if token:
            invite = Invite._base_manager.filter(token=token).first()
            
            # If invite is marked as used, verify if the user actually exists
            if invite and invite.used_at:
                from django.contrib.auth.models import User
                if User.objects.filter(email=invite.email).exists():
                    logger.warning(f"Registration blocked: Invite token '{token}' is already used by an existing user.")
                    invite = None  # Truly used, block access
                else:
                    logger.info(f"Token '{token}' used_at is set but user doesn't exist. Allowing registration.")
            elif invite:
                logger.info(f"Invite token '{token}' validated successfully.")
            else:
                logger.warning(f"Invite token '{token}' not found in database.")
        else:
            invite = None
    except ValidationError:
        logger.warning(f"Invite token '{token}' failed validation.")
        invite = None

    if not invite:
        messages.error(request, "Invalid, expired, or missing invitation.")
        if 'invite_token' in request.session:
            del request.session['invite_token']
        return redirect('login')

    if invite:
        # Force the tenant context to match the invite for form rendering and validation
        request.tenant = invite.tenant
        set_current_tenant(invite.tenant)
    else:
        # Open registration allowed: no specific tenant scoped yet
        request.tenant = None
        set_current_tenant(None)

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            try:
                user = form.save(commit=False)
                # Need to manually set username as email since form uses AbstractUser
                user.username = form.cleaned_data.get('email')
                user.save()

                logger.info(f"User created: {user.email} (ID: {user.id}) via token '{token}'")

                selected_dept = form.cleaned_data.get('department')
                user.profile.department = selected_dept
                user.profile.phone = form.cleaned_data.get('phone')
                
                # Assign to the correct tenant explicitly
                if invite:
                    user.profile.tenant = invite.tenant
                elif selected_dept and getattr(selected_dept, 'tenant', None):
                    user.profile.tenant = selected_dept.tenant
                else:
                    # Fallback default tenant
                    fallback_tenant, _ = Tenant.objects.get_or_create(subdomain='default', defaults={'name': 'Default'})
                    user.profile.tenant = fallback_tenant
                    
                user.profile.save()

                logger.info(f"Profile updated: Tenant '{user.profile.tenant.subdomain}' assigned.")

                if invite:
                    invite.used_at = timezone.now()
                    invite.save()

                if 'invite_token' in request.session:
                    del request.session['invite_token']

                # Explicitly set backend so django does not drop the session over missing backend
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                logger.info(f"User {user.email} successfully authenticated. Redirecting to dashboard...")

                messages.success(request, "Registration successful! You are now logged in.")
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Registration failed due to exception: {str(e)}")
                form.add_error(None, f"An error occurred during registration: {str(e)}")
        else:
            logger.error(f"Registration form validation failed: {form.errors}")

    else:
        if invite:
            request.session['invite_token'] = str(invite.token)
            form = UserRegisterForm(initial={'email': invite.email})
        else:
            form = UserRegisterForm()

    return render(request, 'gameplay/register.html', {'form': form, 'token': token})

# 10. Organizer adds lessons to a training
def manage_lessons(request, training_id):
    training = get_object_or_404(Training, pk=training_id, tenant=request.tenant)
    
    # Security: Only the organizer can manage lessons
    if request.user != training.organizer:
        return redirect('training_page')

    if request.method == 'POST':
        # request.FILES is required for the attached slides/documents
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.training = training
            lesson.tenant = request.tenant
            lesson.save()
            return redirect('manage_lessons', training_id=training.id)
    else:
        form = LessonForm(initial={'order': training.lessons.count() + 1})

    lessons = training.lessons.all()
    return render(request, 'gameplay/manage_lessons.html', {
        'training': training, 
        'form': form, 
        'lessons': lessons
    })

# 11. Attendees view the actual lesson
def view_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id, tenant=request.tenant)
    training = lesson.training
    
    # Security: Must be registered to view
    if request.user not in training.attendees.all() and request.user != training.organizer:
        return redirect('training_page')
        
    return render(request, 'gameplay/view_lesson.html', {'lesson': lesson, 'training': training})

# 12. Department Profile Page
def department_detail(request, department_id):
    department = get_object_or_404(Department, pk=department_id, tenant=request.tenant)
    questions = department.questions.all()
    
    has_taken_quiz = QuizResult.objects.filter(user=request.user, department=department).exists()
    total_score = department.profile_set.aggregate(sum=Sum('total_score'))['sum'] or 0

    video_embed_url = None
    if department.video_url:
        regex = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
        match = re.search(regex, department.video_url)
        
        if match:
            video_id = match.group(1)
            video_embed_url = f"https://www.youtube.com/embed/{video_id}"

    # Count how many ideas this specific department has accepted/installed
    accepted_ideas_count = department.installed_ideas.count()
    
    # Count how many total ideas exist that this department HAS NOT accepted yet
    new_ideas_count = Idea.objects.filter(tenant=request.tenant).exclude(accepted_by=department).count()

    return render(request, 'gameplay/department_detail.html', {
        'department': department,
        'questions': questions,
        'has_taken_quiz': has_taken_quiz,
        'total_score': total_score,
        'video_embed_url': video_embed_url, 
        'accepted_ideas_count': accepted_ideas_count,
        'new_ideas_count': new_ideas_count,
    })

# 13. Add Questions to Department
def add_department_question(request, department_id):
    department = get_object_or_404(Department, pk=department_id, tenant=request.tenant)
    
    # Only superusers (Master Admins) or the assigned Tenant Admin should edit department quizzes
    is_tenant_admin = getattr(request.tenant, 'tenant_admin_id', None) == request.user.id
    if not request.user.is_superuser and not is_tenant_admin:
        return redirect('department_detail', department_id=department.id)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.department = department 
            question.tenant = request.tenant
            question.save()
            return redirect('add_department_question', department_id=department.id)
    else:
        form = QuestionForm()

    return render(request, 'gameplay/add_department_question.html', {
        'department': department, 
        'form': form,
        'questions': department.questions.all()
    })

# 14. Take Department Quiz
def take_department_quiz(request, department_id):
    department = get_object_or_404(Department, pk=department_id, tenant=request.tenant)
    questions = department.questions.all()

    # Prevent taking it twice
    if QuizResult.objects.filter(user=request.user, department=department).exists():
        return redirect('department_detail', department_id=department.id)

    if request.method == 'POST':
        score = 0
        feedback = []

        for q in questions:
            selected = request.POST.get(f'question_{q.id}')
            is_correct = (selected == q.correct_option)
            
            if is_correct:
                score += 1
            
            # Save the details of this specific question
            feedback.append({
                'question_obj': q,
                'selected': selected,
                'correct_answer': q.correct_option,
                'is_correct': is_correct
            })

        QuizResult.objects.create(department=department, user=request.user, score=score, tenant=request.tenant)
        
        # Give Points
        points_earned = score * 10
        request.user.profile.total_score += points_earned
        request.user.profile.save()

        return render(request, 'gameplay/quiz_results.html', {
            'score': score,
            'total_questions': questions.count(),
            'feedback': feedback,
            'is_department_quiz': True,       
            'department_id': department.id    
        })

    return render(request, 'gameplay/take_quiz.html', {
        'training': department,
        'questions': questions
    })

def campus_map(request):
    if not request.tenant:
        messages.info(request, "Please select an organization to view the campus map.")
        departments = Department.objects.none()
    else:
        departments = Department.objects.filter(tenant=request.tenant).prefetch_related('question_set')

    # Gather total points for each department
    dept_data = []
    for dept in departments:
        total = dept.total_points()  # adjust to however you calculate points
        dept_data.append({
            'dept': dept,
            'total_points': total,
        })

    # Find the max points to scale heights proportionally
    max_points = max((d['total_points'] for d in dept_data), default=1)
    if max_points == 0:
        max_points = 1  # avoid division by zero

    # Scale: min height = 30px, max height = 200px
    MIN_HEIGHT = 30
    MAX_HEIGHT = 200

    for d in dept_data:
        ratio = d['total_points'] / max_points
        d['dept'].building_height = int(MIN_HEIGHT + ratio * (MAX_HEIGHT - MIN_HEIGHT))
        d['dept'].total_points = d['total_points']

    # Slug mapping for CSS classes (adjust to match your department names)
    slug_map = {
        'IT': 'it',
        'HR': 'hr',
        'Logistics': 'logs',
        'Operations': 'ops',
        'Safety': 'safe',
        'Maintenance': 'maint',
    }
    for d in dept_data:
        ratio = (d['total_points'] / max_points) ** 0.5
        
        d['dept'].building_height = int(MIN_HEIGHT + ratio * (MAX_HEIGHT - MIN_HEIGHT))
        d['dept'].total_points = d['total_points']

    context = {
        'departments': [d['dept'] for d in dept_data],
    }
    return render(request, 'gameplay/campus_map.html', context)

@login_required
def accept_idea(request, idea_id):
    is_tenant_admin = getattr(request.tenant, 'tenant_admin_id', None) == request.user.id
    if not request.user.is_superuser and not is_tenant_admin:
        messages.error(request, "Only company admins can approve ideas.")
        return redirect('ideas_page')

    idea = get_object_or_404(Idea, pk=idea_id, tenant=request.tenant)
    
    # We check the Admin's department so we know WHO is accepting the idea
    if hasattr(request.user, 'profile') and request.user.profile.department:
        admin_dept = request.user.profile.department
        
        # Add the department to the idea's "accepted" list
        idea.accepted_by.add(admin_dept)
        messages.success(request, f"Idea successfully installed for {admin_dept.name}!")
        
        # Bonus: Give the person who submitted the idea 100 points!
        if idea.submitted_by and hasattr(idea.submitted_by, 'profile'):
            idea.submitted_by.profile.total_score += 100
            idea.submitted_by.profile.save()
            messages.success(request, f"100 bonus points automatically awarded to {idea.submitted_by.username}!")
            
    else:
        messages.error(request, "You must be assigned to a department to accept ideas.")
        
    return redirect('ideas_page')

@login_required
def submit_feedback(request, training_id):
    if request.method == 'POST':
        training = get_object_or_404(Training, pk=training_id, tenant=request.tenant)
        rating = request.POST.get('rating')
        suggestions = request.POST.get('suggestions')

        # Prevent duplicate feedback from the same user
        if not TrainingFeedback.objects.filter(training=training, user=request.user).exists():
            TrainingFeedback.objects.create(
                training=training,
                user=request.user,
                rating=rating,
                suggestions=suggestions,
                tenant=request.tenant
            )
            messages.success(request, "Thank you! Your feedback has been sent to the organizer.")
            
        return redirect('training_page')
    return redirect('dashboard')

# 15. Problems Page (Form + List of unsolved problems)
@login_required
def problems_page(request):
    if request.method == 'POST':
        if not request.tenant:
            messages.error(request, "You must select an organization first.")
            return redirect('problems_page')
            
        form = ProblemForm(request.POST)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.submitted_by = request.user
            problem.tenant = request.tenant
            problem.save()
            messages.success(request, "Your problem has been shared! A fellow employee might help solve it.")
            return redirect('problems_page')
    else:
        form = ProblemForm()

    # List problems that are not yet confirmed solved, newest first
    if not request.tenant:
        messages.info(request, "Please select an organization to view problems.")
        unsolved_problems = Problem.objects.none()
    else:
        unsolved_problems = Problem.objects.filter(is_solved=False, tenant=request.tenant).order_by('-submitted_at')
    
    return render(request, 'gameplay/problems.html', {
        'form': form,
        'problems': unsolved_problems,
    })

# 16. A helper claims they solved a problem
@login_required
def claim_solution(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id, tenant=request.tenant)
    
    if problem.submitted_by == request.user:
        messages.error(request, "You cannot solve your own problem!")
        return redirect('problems_page')
    elif problem.is_solved or problem.is_claimed_solved:
        messages.error(request, "This problem is already being handled.")
        return redirect('problems_page')

    # If the user submits the form
    if request.method == 'POST':
        # request.FILES is required for the image upload!
        form = SolutionForm(request.POST, request.FILES, instance=problem)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.claimed_by = request.user
            problem.is_claimed_solved = True
            problem.save()
            messages.success(request, f"Your solution has been sent to {problem.submitted_by.username} for review!")
            return redirect('problems_page')
    else:
        form = SolutionForm(instance=problem)
        
    return render(request, 'gameplay/submit_solution.html', {'form': form, 'problem': problem})

# 17. The submitter confirms the solution works (The big reward point view)
@login_required
def confirm_solved(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id, tenant=request.tenant)
    
    # Security: Only the original submitter can confirm the solution
    if problem.submitted_by != request.user:
        messages.error(request, "Only the person who shared the problem can confirm the solution.")
        return redirect('profile_page')
    
    # Security: Solution must be claimed first, and prevent duplicate confirming
    if not problem.is_claimed_solved or not problem.claimed_by:
        messages.error(request, "No one has claimed to solve this problem yet.")
        return redirect('profile_page')
    
    if problem.is_solved:
        messages.error(request, "This problem has already been confirmed.")
        return redirect('profile_page')
        
    # --- STEP 2: Give the Reward Points! (+10 points) ---
    # Find the helper who claimed the solution
    helper_profile = problem.claimed_by.profile
    
    # Give the points bonus
    helper_profile.total_score += 10
    helper_profile.save()
    
    # Step 3: Finalize the problem
    problem.is_solved = True
    problem.solved_at = timezone.now()
    problem.save()
    
    messages.success(request, f"Perfect! The problem is confirmed solved. +10 points added to {problem.claimed_by.username}'s profile!")
    return redirect('profile_page')

# 18. Submitter rejects the solution
@login_required
def reject_solution(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id, tenant=request.tenant)
    
    if problem.submitted_by != request.user:
        messages.error(request, "Only the person who shared the problem can reject a solution.")
        return redirect('profile_page')

    # Revert to "unsolved", clear the helper's claim, text, and image
    problem.claimed_by = None
    problem.is_claimed_solved = False
    problem.solution_description = None
    problem.solution_image = None
    problem.save()
    
    messages.success(request, "Solution rejected. The problem is now listed for others to solve.")
    return redirect('profile_page')

# 19. Redeem Gift Card Page
@login_required
def redeem_page(request):
    if request.method == 'POST':
        reward_tier = request.POST.get('reward_tier')
        store_choice = request.POST.get('store_choice', 'Generic')
        
        # Define reward costs and values
        rewards = {
            '20': {'points': 100, 'euros': 20, 'name': '20€ Gift Card'},
            '50': {'points': 200, 'euros': 50, 'name': '50€ Gift Card'},
            '100': {'points': 350, 'euros': 100, 'name': '100€ VIP Gift Card'},
        }

        if reward_tier in rewards:
            reward = rewards[reward_tier]
            if request.user.profile.total_score >= reward['points']:
                request.user.profile.total_score -= reward['points']
                request.user.profile.bonus_euros += reward['euros']
                request.user.profile.save()
                
                from .models import RedeemedReward
                RedeemedReward.objects.create(
                    user=request.user,
                    store=store_choice,
                    amount=reward['euros']
                )

                messages.success(request, f"Success! You have redeemed {reward['points']} points for a {reward['name']} at {store_choice}! Check your profile balance.")
            else:
                messages.error(request, f"Not enough points! You need at least {reward['points']} points for this reward.")
        else:
            messages.error(request, "Invalid reward selected.")
            
        return redirect('redeem_page')
        
    return render(request, 'gameplay/redeem.html', {'profile': request.user.profile})

# 20. Admin Bulk Invite Upload
@staff_member_required
def bulk_invite_upload(request):
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant')
        csv_file = request.FILES.get('csv_file')
        
        if not tenant_id or not csv_file:
            messages.error(request, "Please select an organization and upload a file.")
            return redirect('admin:gameplay_invite_bulk')
            
        is_csv = csv_file.name.lower().endswith('.csv')
        is_txt = csv_file.name.lower().endswith('.txt')
        
        if not (is_csv or is_txt):
            messages.error(request, "The uploaded file must be a .csv or .txt file.")
            return redirect('admin:gameplay_invite_bulk')
        
        tenant = get_object_or_404(Tenant, pk=tenant_id)
        
        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
        except Exception as e:
            messages.error(request, f"Error reading file: {e}")
            return redirect('admin:gameplay_invite_bulk')
        
        summary = {'created': 0, 'skipped': 0, 'refreshed': 0, 'errors': 0, 'emails_sent': 0, 'emails_failed': 0, 'email_error_details': []}
        
        if not getattr(settings, 'EMAIL_HOST', None) or not getattr(settings, 'EMAIL_HOST_USER', None) or not getattr(settings, 'EMAIL_HOST_PASSWORD', None):
            summary['email_error'] = "Email settings (EMAIL_HOST / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD) are missing. Emails will not be sent."
            messages.error(request, "SMTP configuration is missing. Emails will not be sent.")
        else:
            logger.info(f"SMTP Config: HOST={getattr(settings, 'EMAIL_HOST', None)}, "
                        f"PORT={getattr(settings, 'EMAIL_PORT', None)}, "
                        f"TLS={getattr(settings, 'EMAIL_USE_TLS', None)}, "
                        f"USER={getattr(settings, 'EMAIL_HOST_USER', None)}, "
                        f"FROM={getattr(settings, 'DEFAULT_FROM_EMAIL', None)}")
        results = []

        if is_csv:
            reader = csv.reader(io.StringIO(decoded_file))
            header = next(reader, None)
            
            if not header:
                messages.error(request, "The CSV file is empty.")
                return redirect('admin:gameplay_invite_bulk')
            
            email_idx = 0
            lower_header = [str(h).strip().lower() for h in header]
            if 'email' in lower_header:
                email_idx = lower_header.index('email')
            else:
                # If there's no header row, process the very first row as data
                _process_csv_email(header[email_idx], tenant, request, results, summary)
            
            for row in reader:
                if row and len(row) > email_idx:
                    _process_csv_email(row[email_idx], tenant, request, results, summary)
        else:
            lines = decoded_file.splitlines()
            if not lines:
                messages.error(request, "The TXT file is empty.")
                return redirect('admin:gameplay_invite_bulk')
                
            for line in lines:
                line = line.strip()
                if line:
                    _process_csv_email(line, tenant, request, results, summary)
                
        if summary['emails_failed'] > 0:
            err_details = " | ".join(summary['email_error_details'])
            messages.error(request, f"{summary['emails_failed']} email(s) failed to send. Details: {err_details}")

        return render(request, 'gameplay/bulk_invite_results.html', {
            'results': results, 
            'summary': summary,
            'tenant': tenant
        })
    
    tenants = Tenant.objects.all().order_by('name')
    return render(request, 'gameplay/bulk_invite.html', {'tenants': tenants})

def _send_invite_email(email, tenant, link):
    if not getattr(settings, 'EMAIL_HOST', None) or not getattr(settings, 'EMAIL_HOST_USER', None) or not getattr(settings, 'EMAIL_HOST_PASSWORD', None):
        return False, "Missing SMTP configuration"
        
    subject = f"You're invited to join {tenant.name}"
    message = f"You're invited to join {tenant.name}.\n\nPlease sign up using the following link:\n{link}"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
    try:
        send_mail(subject, message, from_email, [email], fail_silently=False)
        return True, None
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return False, str(e)

def _process_csv_email(raw_email, tenant, request, results, summary):
    try:
        email = raw_email.strip().lower()
        if not email:
            return
        
        logger.info(f"Processing bulk invite for: {email} (Tenant: {tenant.name})")
        
        # Deduce the host cleanly (e.g. stripping existing subdomains or 'www.')
        base_host = request.get_host()
        if base_host.startswith('www.'):
            base_host = base_host[4:]
        for t in Tenant.objects.all():
            if base_host.startswith(t.subdomain + '.'):
                base_host = base_host[len(t.subdomain)+1:]
                break
                
        invite = Invite.objects.filter(email=email, tenant=tenant).first()
        
        if invite:
            if invite.used_at:
                logger.info(f" -> Skipped (Already registered)")
                results.append({'email': email, 'status': 'Skipped (Already Used)', 'link': ''})
                summary['skipped'] += 1
            else:
                # Refresh token for unused invites
                invite.token = uuid.uuid4()
                invite.save()
                link = f"{request.scheme}://{tenant.subdomain}.{base_host}/signup/?token={invite.token}"
                summary['refreshed'] += 1
                
                email_sent, email_err = _send_invite_email(email, tenant, link)
                if email_sent:
                    logger.info(f" -> Refreshed existing token and sent email")
                    results.append({'email': email, 'status': 'Refreshed + Sent', 'link': link})
                    summary['emails_sent'] += 1
                else:
                    logger.info(f" -> Refreshed existing token but email failed")
                    results.append({'email': email, 'status': 'Refreshed + Failed', 'link': link})
                    summary['emails_failed'] += 1
                    if email_err and email_err not in summary['email_error_details']:
                        summary['email_error_details'].append(email_err)
        else:
            invite = Invite.objects.create(email=email, tenant=tenant)
            link = f"{request.scheme}://{tenant.subdomain}.{base_host}/signup/?token={invite.token}"
            summary['created'] += 1
            
            email_sent, email_err = _send_invite_email(email, tenant, link)
            if email_sent:
                logger.info(f" -> Created successfully and sent email")
                results.append({'email': email, 'status': 'Created + Sent', 'link': link})
                summary['emails_sent'] += 1
            else:
                logger.info(f" -> Created successfully but email failed")
                results.append({'email': email, 'status': 'Created + Failed', 'link': link})
                summary['emails_failed'] += 1
                if email_err and email_err not in summary['email_error_details']:
                    summary['email_error_details'].append(email_err)
    except Exception as e:
        logger.error(f"Error processing invite for {raw_email}: {str(e)}")
        results.append({'email': raw_email, 'status': f'Error: {str(e)}', 'link': ''})
        summary['errors'] += 1