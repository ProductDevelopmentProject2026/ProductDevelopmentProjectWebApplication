from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .thread_local import get_current_tenant
import uuid

class Tenant(models.Model):
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TenantManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs

class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    objects = TenantManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            tenant = get_current_tenant()
            if not tenant:
                # Fallback for management commands, shell, or background tasks
                tenant, _ = Tenant.objects.get_or_create(
                    subdomain='default',
                    defaults={'name': 'Default Organization'}
                )
            if tenant:
                self.tenant = tenant
        super().save(*args, **kwargs)

class Invite(TenantAwareModel):
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('tenant', 'email')

    def __str__(self):
        return f"{self.email} ({self.tenant.name})"

# 1. Departments for the "Battle" (Logistics vs Accounting)
class Department(TenantAwareModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text="What does this team do?")
    video_url = models.URLField(blank=True, null=True, help_text="YouTube intro video")

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('tenant', 'name')

# 2. Employee Profile to track their Department
class Profile(TenantAwareModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    total_score = models.IntegerField(default=0)
    bonus_euros = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} ({self.department})"
    
    @property
    def total_problems_solved(self):
        """Calculates total problems this user helped solve, which are confirmed by the submitter."""
        # Find problems where this user is the "claimed_by" and the original submitter confirmed "is_solved=True"
        return Problem.objects.filter(claimed_by=self.user, is_solved=True, tenant=self.tenant).count()

# 3. To track actions like "Safety Test" or "Kilometers"
class ActionLog(TenantAwareModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_name = models.CharField(max_length=200) # e.g. "Passed Safety Test"
    points = models.IntegerField(default=10)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action_name} (+{self.points})"

class IdeaCategory(TenantAwareModel):
    name = models.CharField(max_length=100)
    keywords = models.TextField(help_text="Comma-separated keywords for auto-identification")

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('tenant', 'name')

# 4. For the "Ideas Marathon" (Kaizen)
class Idea(TenantAwareModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    voters = models.ManyToManyField(User, related_name='voted_ideas', blank=True)
    
    is_anonymous = models.BooleanField(default=False)
    
    accepted_by = models.ManyToManyField('Department', related_name='installed_ideas', blank=True)
    category = models.ForeignKey(IdeaCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='ideas')

    def __str__(self):
        return self.title
    
class Training(TenantAwareModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date_time = models.DateTimeField()
    location = models.CharField(max_length=100)
    
    image = models.ImageField(upload_to='training_images/', blank=True, null=True)
    
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_trainings')
    attendees = models.ManyToManyField(User, related_name='attended_trainings', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        unique_together = ('tenant', 'title')

class Question(TenantAwareModel):
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    
    text = models.CharField(max_length=300)
    option_1 = models.CharField(max_length=200)
    option_2 = models.CharField(max_length=200)
    option_3 = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[('1', 'Option 1'), ('2', 'Option 2'), ('3', 'Option 3')])

    def __str__(self):
        return self.text

class QuizResult(TenantAwareModel):
    training = models.ForeignKey(Training, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # This try/except block prevents crashes if the profile doesn't exist yet
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

class Lesson(TenantAwareModel):
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, help_text="Main text for the lesson")
    video_url = models.URLField(blank=True, null=True, help_text="Paste a YouTube or Vimeo link")
    attached_file = models.FileField(upload_to='training_files/', blank=True, null=True)
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.training.title} - {self.order}. {self.title}"

class TrainingFeedback(TenantAwareModel):
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5) 
    suggestions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.training.title} ({self.rating} Stars)"

class Problem(TenantAwareModel):
    description = models.TextField()
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_problems')
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Track who claimed to solve it and when
    claimed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='claimed_solutions')
    is_claimed_solved = models.BooleanField(default=False)
    
    solution_description = models.TextField(blank=True, null=True)
    solution_image = models.ImageField(upload_to='solutions/', blank=True, null=True)

    # Track when the original submitter confirms it is solved
    is_solved = models.BooleanField(default=False)
    solved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.submitted_by.username}'s problem (Solved: {self.is_solved})"