from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum
from .models import Department, Idea, Profile, Training, Question, QuizResult
from .forms import IdeaForm, TrainingForm, QuestionForm           
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

# 1. Home Page (Welcome)
def dashboard(request):
    return render(request, 'gameplay/dashboard.html')

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
            return redirect('ideas_page') # Stay on this page
    else:
        form = IdeaForm()

    # Get ideas sorted by votes
    pending_ideas = Idea.objects.annotate(num_votes=Count('voters')).filter(is_approved=False).order_by('-num_votes')
    
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
    # This fetches the profile for the person who is logged in
    user_profile = get_object_or_404(Profile, user=request.user)
    # Fetch ideas submitted by this specific user
    my_ideas = Idea.objects.filter(submitted_by=request.user)
    
    return render(request, 'gameplay/profile.html', {
        'profile': user_profile,
        'my_ideas': my_ideas
    })

# 5. Training Page (List + Create)
def training_page(request):
    # Handle "Add Training" form
    if request.method == 'POST':
        form = TrainingForm(request.POST, request.FILES)
        if form.is_valid():
            new_training = form.save(commit=False)
            new_training.organizer = request.user
            new_training.save()
            return redirect('training_page')
    else:
        form = TrainingForm()

    # Get all trainings, sorted by newest first
    trainings = Training.objects.all().order_by('date_time')

    return render(request, 'gameplay/training.html', {
        'trainings': trainings, 
        'form': form
    })

# 6. Registration Logic (Like Voting)
def register_training(request, training_id):
    training = get_object_or_404(Training, pk=training_id)

    if request.user.is_authenticated:
        if request.user in training.attendees.all():
            training.attendees.remove(request.user) # Un-register
        else:
            training.attendees.add(request.user)    # Register

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
        for q in questions:
            selected_option = request.POST.get(f'question_{q.id}')
            if selected_option == q.correct_option:
                score += 1
        
        QuizResult.objects.create(training=training, user=request.user, score=score)
        
        request.user.profile.total_score += (score * 10)
        request.user.profile.save()

        return redirect('training_page')

    return render(request, 'gameplay/take_quiz.html', {'training': training, 'questions': questions})

# 9. Registration Page
def register_page(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after signing up
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()

    return render(request, 'gameplay/register.html', {'form': form})