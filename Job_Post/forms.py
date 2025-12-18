from django import forms
from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title',
            'tags',
            'job_type',
            'min_salary',
            'max_salary',
            'negotiable',
            'description',
            'responsibilities',
        ]

        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Job title'}),
            'tags': forms.TextInput(attrs={'placeholder': 'Tags / Keywords'}),

            'job_type': forms.Select(),

            'min_salary': forms.NumberInput(attrs={'placeholder': 'Minimum salary (Nrs)'}),
            'max_salary': forms.NumberInput(attrs={'placeholder': 'Maximum salary (Nrs)'}),

            'description': forms.Textarea(attrs={'rows': 4}),
            'responsibilities': forms.Textarea(attrs={'rows': 4}),
        }
