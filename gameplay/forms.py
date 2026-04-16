from django import forms
from .models import Idea, Training, Question, Lesson, Profile
from django.contrib.auth.models import User
from .models import Department, Problem
from django.contrib.auth.forms import UserCreationForm

class EmployeeEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.none(), required=False)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        self.profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['department'].queryset = Department.objects.filter(tenant=self.tenant)
        if self.profile:
            self.fields['department'].initial = self.profile.department
            self.fields['phone'].initial = self.profile.phone
            
        for field in self.fields.values():
            field.widget.attrs.update({'style': 'padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px; box-sizing: border-box;'})

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            if self.profile:
                self.profile.department = self.cleaned_data['department']
                self.profile.phone = self.cleaned_data['phone']
                self.profile.save()
        return user

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
    first_name = forms.CharField(max_length=30, required=False, help_text="Optional. Your first name.")
    last_name = forms.CharField(max_length=30, required=False, help_text="Optional. Your last name.")
    phone = forms.CharField(max_length=20, required=False, help_text="Optional. Your phone number.")

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
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['description'] # User only types the description
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe your problem here...'})
        }

class SolutionForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['solution_description', 'solution_image']
        labels = {
            'solution_description': 'Step-by-Step Explanation',
            'solution_image': 'Attach a Screenshot (Optional)'
        }
        widgets = {
            'solution_description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Explain exactly how to fix this issue...'}),
        }