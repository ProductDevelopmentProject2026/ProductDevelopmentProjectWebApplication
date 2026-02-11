from django.shortcuts import render, redirect, get_object_or_404
from .models import Department, Idea
from .forms import IdeaForm
from django.db.models import Count

def dashboard(request):
    if request.method == 'POST':
        form = IdeaForm(request.POST)
        if form.is_valid():
            new_idea = form.save(commit=False)
            # ALWAYS save the real user (so Admin knows)
            new_idea.submitted_by = request.user
            new_idea.save()
            return redirect('dashboard')
    else:
        form = IdeaForm()

    all_departments = Department.objects.all()
    
    # Keep this logic to count votes correctly
    pending_ideas = Idea.objects.annotate(num_votes=Count('voters')).filter(is_approved=False).order_by('-num_votes')

    context = {
        'departments': all_departments,
        'ideas': pending_ideas,
        'form': form,
    }
    
    return render(request, 'gameplay/dashboard.html', context)

def vote_idea(request, idea_id):
    # 1. Get the idea
    idea = get_object_or_404(Idea, pk=idea_id)
    
    # 2. Check if the user is logged in
    if request.user.is_authenticated:
        # 3. Check if they are already in the "voters" list
        if request.user in idea.voters.all():
            # (Optional) If they already voted, remove their vote? (Toggle)
            idea.voters.remove(request.user)
        else:
            # If they haven't voted, add them
            idea.voters.add(request.user)

    # 4. Refresh the page
    return redirect('dashboard')