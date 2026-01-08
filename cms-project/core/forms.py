"""
Forms for the Complaint Management System.
"""

from django import forms
from django.contrib.auth.models import User
from .models import Complaint, UserProfile


class ComplaintForm(forms.ModelForm):
    """Form for creating/editing complaints."""
    
    submitted_by = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label='On behalf of (Consumer)',
        help_text='Select a consumer if logging on their behalf'
    )
    
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'priority', 'submitted_by']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of your complaint'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Provide detailed information about your complaint'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Billing, Technical, Service'
            }),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        if user and hasattr(user, 'profile'):
            profile = user.profile
            
            if profile.is_consumer():
                del self.fields['submitted_by']
            else:
                consumers = User.objects.filter(
                    profile__tenant=profile.tenant,
                    profile__role=UserProfile.ROLE_CONSUMER
                )
                self.fields['submitted_by'].queryset = consumers
                self.fields['submitted_by'].widget.attrs['class'] = 'form-control'


class ComplaintStatusForm(forms.ModelForm):
    """Form for updating complaint status."""
    
    class Meta:
        model = Complaint
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'})
        }


class AssignmentForm(forms.Form):
    """Form for assigning complaints to support staff."""
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='Assign to',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if tenant:
            support_staff = User.objects.filter(
                profile__tenant=tenant,
                profile__role__in=[UserProfile.ROLE_SUPPORT, UserProfile.ROLE_MANAGER]
            )
            self.fields['assigned_to'].queryset = support_staff


class ResolutionForm(forms.Form):
    """Form for adding resolution notes."""
    
    resolution_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter resolution details...'
        }),
        label='Resolution Notes'
    )
