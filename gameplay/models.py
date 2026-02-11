from django.db import models
from django.contrib.auth.models import User

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
    
    # NEW: The checkbox to hide the name
    is_anonymous = models.BooleanField(default=False)
    
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title