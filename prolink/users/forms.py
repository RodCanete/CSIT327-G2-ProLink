from django import forms
from .models import Profile  # We'll create Profile next

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']
