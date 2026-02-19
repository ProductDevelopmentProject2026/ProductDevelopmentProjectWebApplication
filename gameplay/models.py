from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1. Departments for the "Battle" (Logistics vs Accounting)
class Department(models.Model):
    name = models.CharField(max_length=100) # e.g. "Logistics"
    
    def __str__(self):
        return self.name

# 2. Employee Profile to track their Department
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} ({self.department})"

# 3. To track actions like "Safety Test" or "Kilometers"
class ActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_name = models.CharField(max_length=200) # e.g. "Passed Safety Test"
    points = models.IntegerField(default=10)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action_name} (+{self.points})"

# 4. For the "Ideas Marathon" (Kaizen)
class Idea(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    voters = models.ManyToManyField(User, related_name='voted_ideas', blank=True)
    
    is_anonymous = models.BooleanField(default=False)
    
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
class Training(models.Model):
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

class Question(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=300)
    option_1 = models.CharField(max_length=200)
    option_2 = models.CharField(max_length=200)
    option_3 = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[('1', 'Option 1'), ('2', 'Option 2'), ('3', 'Option 3')])

    def __str__(self):
        return self.text

class QuizResult(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} scored {self.score} in {self.training.title}"
    
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