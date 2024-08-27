from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Profile

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['address', 'phone_number']

class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']
