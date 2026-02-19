from django import forms
from .models import Idea, Training, Question

class IdeaForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = ['title', 'description', 'is_anonymous'] 
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Idea Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your idea...', 'rows': 3}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_anonymous': 'Hide my name (Post Anonymously)',
        }

class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ['title', 'description', 'date_time', 'location', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Training Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'What will we learn?', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Room or Link'}),
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'option_1', 'option_2', 'option_3', 'correct_option']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. What is the capital of France?'}),
            'option_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 1'}),
            'option_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 2'}),
            'option_3': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 3'}),
            'correct_option': forms.Select(attrs={'class': 'form-control'}),
        }