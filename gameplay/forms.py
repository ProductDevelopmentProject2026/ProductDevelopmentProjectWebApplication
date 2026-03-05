from django import forms
from .models import Idea, Training, Question, Lesson
from django.contrib.auth.models import User
from .models import Department
from django.contrib.auth.forms import UserCreationForm


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

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['order', 'title', 'content', 'video_url', 'attached_file']
        widgets = {
            'order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lesson Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write the lesson text here...', 'rows': 5}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            'attached_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        help_text="Required. Please enter a valid email address."
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        help_text="Select the department you belong to."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)
