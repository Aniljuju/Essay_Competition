from django import forms
from django.contrib.auth.models import User
from .models import Competition, Paragraph, UserProfile


class ParagraphForm(forms.ModelForm):
    """
    Form for submitting a paragraph
    """
    class Meta:
        model = Paragraph
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Write your paragraph here...',
                'required': True,
            }),
        }
        labels = {
            'content': 'Paragraph Content',
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content:
            raise forms.ValidationError('Paragraph content cannot be empty.')
        if len(content) < 50:
            raise forms.ValidationError('Paragraph must be at least 50 characters long.')
        return content


class CompetitionForm(forms.ModelForm):
    """
    Form for creating/editing competitions (admin only)
    """
    class Meta:
        model = Competition
        fields = ['title', 'description', 'start_date', 'end_date', 'max_paragraphs']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_paragraphs': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError('End date must be after start date.')
        
        return cleaned_data


class UserStatusForm(forms.ModelForm):
    """
    Form for changing user verification status (admin only)
    """
    class Meta:
        model = UserProfile
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }