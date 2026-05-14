import re

with open('gameplay/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
@login_required
def analytics_page(request):
    tenant = request.tenant
    if not tenant:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Organization must be selected.")
        return redirect('dashboard')
        
    from datetime import timedelta
    from django.db.models import Sum, Count
    from django.utils import timezone
    
    ideas_submitted = Idea.objects.filter(tenant=tenant).count()
    ideas_accepted = Idea.objects.filter(tenant=tenant, accepted_by__isnull=False).distinct().count()
    acceptance_rate = int((ideas_accepted / ideas_submitted * 100)) if ideas_submitted > 0 else 0
    
    problems_raised = Problem.objects.filter(tenant=tenant).count()
    problems_resolved = Problem.objects.filter(tenant=tenant, is_solved=True).count()
    resolved_rate = int((problems_resolved / problems_raised * 100)) if problems_raised > 0 else 0
    
    team_members = Profile.objects.filter(tenant=tenant).count()
    
    month_ago = timezone.now() - timedelta(days=30)
    active_this_month = ActionLog.objects.filter(tenant=tenant, date_created__gte=month_ago).values('user').distinct().count()
    engagement_rate = int((active_this_month / team_members * 100)) if team_members > 0 else 0
    
    points_agg = Profile.objects.filter(tenant=tenant).aggregate(Sum('total_score'), Sum('bonus_euros'))
    total_points = points_agg['total_score__sum'] or 0
    total_bonuses = points_agg['bonus_euros__sum'] or 0
    
    quizzes_completed = QuizResult.objects.filter(tenant=tenant).count()
    trainings_created = Training.objects.filter(tenant=tenant).count()
    training_enrollments = Training.objects.filter(tenant=tenant).aggregate(Count('attendees'))['attendees__count'] or 0
    
    week_ago = timezone.now() - timedelta(days=7)
    active_last_7_days = ActionLog.objects.filter(tenant=tenant, date_created__gte=week_ago).values('user').distinct().count()

    context = {
        'ideas_submitted': ideas_submitted,
        'ideas_accepted': ideas_accepted,
        'acceptance_rate': acceptance_rate,
        'problems_raised': problems_raised,
        'problems_resolved': problems_resolved,
        'resolved_rate': resolved_rate,
        'team_members': team_members,
        'active_this_month': active_this_month,
        'engagement_rate': engagement_rate,
        'total_points': total_points,
        'total_bonuses': total_bonuses,
        'quizzes_completed': quizzes_completed,
        'trainings_created': trainings_created,
        'training_enrollments': training_enrollments,
        'active_last_7_days': active_last_7_days
    }
    
    return render(request, 'gameplay/analytics.html', context)

@login_required
def alerts_page(request):
    tenant = request.tenant
    if not tenant:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Organization must be selected.")
        return redirect('dashboard')
        
    action_logs = ActionLog.objects.filter(tenant=tenant).select_related('user').order_by('-date_created')[:20]
    return render(request, 'gameplay/alerts.html', {'action_logs': action_logs})
'''

text = re.sub(
    r'@login_required\s*\ndef analytics_page\(request\):.*?return render\(request, \'gameplay/alerts\.html\'\)',
    replacement.strip(),
    text,
    flags=re.DOTALL
)

with open('gameplay/views.py', 'w', encoding='utf-8') as f:
    f.write(text)