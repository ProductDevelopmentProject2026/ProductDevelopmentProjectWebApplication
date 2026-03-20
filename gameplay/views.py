from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum, Avg
from .models import Department, Idea, Profile, Training, Question, QuizResult, Lesson, TrainingFeedback
from .forms import IdeaForm, TrainingForm, QuestionForm, LessonForm, UserRegisterForm        
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
import re  
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# 1. Home Page (Welcome)
@login_required
def dashboard(request):
    departments = Department.objects.annotate(
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
    # (top%, left%) — keep them away from edges so 80px buildings stay visible
    positions = [
        (15, 30), (15, 60),
        (38, 15), (38, 45), (38, 72),
        (62, 25), (62, 55),
        (80, 15), (80, 45), (80, 72),
    ]

    for i, d in enumerate(dept_data):
        ratio = d['total_points'] / max_points
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
    all_departments = Department.objects.annotate(
        total_points=Sum('profile__total_score')
    ).order_by('-total_points')
    
    return render(request, 'gameplay/departments.html', {'departments': all_departments})

# 3. Ideas Page (Form + List)
def ideas_page(request):
    if request.method == 'POST':
        form = IdeaForm(request.POST)
        if form.is_valid():
            new_idea = form.save(commit=False)
            new_idea.submitted_by = request.user
            new_idea.save()
            return redirect('ideas_page') 
    else:
        form = IdeaForm()

    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.department:
        user_dept = request.user.profile.department
        pending_ideas = Idea.objects.exclude(accepted_by=user_dept).annotate(num_votes=Count('voters')).order_by('-num_votes')
    else:
        pending_ideas = Idea.objects.annotate(num_votes=Count('voters')).order_by('-num_votes')

    return render(request, 'gameplay/ideas.html', {'ideas': pending_ideas, 'form': form})

# 4. Voting Logic
def vote_idea(request, idea_id):
    idea = get_object_or_404(Idea, pk=idea_id)
    if request.user.is_authenticated:
        if request.user in idea.voters.all():
            idea.voters.remove(request.user)
        else:
            idea.voters.add(request.user)
    return redirect('ideas_page') # Go back to ideas page

@login_required
def profile_page(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    my_ideas = Idea.objects.filter(submitted_by=request.user)
    accepted_ideas_count = my_ideas.filter(accepted_by__isnull=False).distinct().count()
    pending_ideas_count = my_ideas.filter(accepted_by__isnull=True).count()

    # --- NEW: Training Analytics Logic ---
    my_trainings = Training.objects.filter(organizer=request.user)
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

    return render(request, 'gameplay/profile.html', {
        'profile': user_profile,
        'my_ideas': my_ideas,
        'accepted_ideas_count': accepted_ideas_count,
        'pending_ideas_count': pending_ideas_count,
        'training_stats': training_stats, # Pass stats to the template
    })

# 5. Training Page (List + Create)
def training_page(request):
    if request.method == 'POST':
        form = TrainingForm(request.POST, request.FILES)
        if form.is_valid():
            new_training = form.save(commit=False)
            new_training.organizer = request.user
            new_training.save()
            
            from django.contrib import messages
            messages.success(request, "Training created! You earned a 50€ bonus.")
            
            return redirect('training_page')
    else:
        form = TrainingForm()

    # Get all trainings, sorted by newest first
    trainings = Training.objects.all().order_by('date_time')

    return render(request, 'gameplay/training.html', {
        'trainings': trainings, 
        'form': form
    })

# 6. Registration Logic (Like Voting), (Updated with Department Block)
def register_training(request, training_id):
    training = get_object_or_404(Training, pk=training_id)

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
    training = get_object_or_404(Training, pk=training_id)
    
    # Security: Only the organizer can add questions
    if request.user != training.organizer:
        return redirect('training_page')

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.training = training
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
    training = get_object_or_404(Training, pk=training_id)
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
        QuizResult.objects.create(training=training, user=request.user, score=score)
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
    if request.method == 'POST':
        form = UserRegisterForm(request.POST) 
        if form.is_valid():
            user = form.save() 
            selected_dept = form.cleaned_data.get('department')
            user.profile.department = selected_dept
            user.profile.save()

            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegisterForm()

    return render(request, 'gameplay/register.html', {'form': form})

# 10. Organizer adds lessons to a training
def manage_lessons(request, training_id):
    training = get_object_or_404(Training, pk=training_id)
    
    # Security: Only the organizer can manage lessons
    if request.user != training.organizer:
        return redirect('training_page')

    if request.method == 'POST':
        # request.FILES is required for the attached slides/documents
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.training = training
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
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    training = lesson.training
    
    # Security: Must be registered to view
    if request.user not in training.attendees.all() and request.user != training.organizer:
        return redirect('training_page')
        
    return render(request, 'gameplay/view_lesson.html', {'lesson': lesson, 'training': training})

# 12. Department Profile Page
def department_detail(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
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
    new_ideas_count = Idea.objects.exclude(accepted_by=department).count()

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
    department = get_object_or_404(Department, pk=department_id)
    
    # Only superusers (Admins) should edit department quizzes
    if not request.user.is_superuser:
        return redirect('department_detail', department_id=department.id)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.department = department 
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
    department = get_object_or_404(Department, pk=department_id)
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

        QuizResult.objects.create(department=department, user=request.user, score=score)
        
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
    departments = Department.objects.prefetch_related('question_set').all()

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
        d['dept'].slug = slug_map.get(d['dept'].name, d['dept'].name.lower())

    context = {
        'departments': [d['dept'] for d in dept_data],
    }
    return render(request, 'gameplay/campus_map.html', context)

@login_required
def accept_idea(request, idea_id):
    if not request.user.is_superuser:
        messages.error(request, "Only admins can approve ideas.")
        return redirect('ideas_page')

    idea = get_object_or_404(Idea, pk=idea_id)
    
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
        training = get_object_or_404(Training, pk=training_id)
        rating = request.POST.get('rating')
        suggestions = request.POST.get('suggestions')

        # Prevent duplicate feedback from the same user
        if not TrainingFeedback.objects.filter(training=training, user=request.user).exists():
            TrainingFeedback.objects.create(
                training=training,
                user=request.user,
                rating=rating,
                suggestions=suggestions
            )
            messages.success(request, "Thank you! Your feedback has been sent to the organizer.")
            
        return redirect('training_page')
    return redirect('dashboard')