from django.contrib.auth.models import User
from django import forms

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-3'}),
        }

class SignupForm(forms.Form):
    username = forms.CharField(label="Full Name", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': '000000', 'type': 'number'}))

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()

class ResetPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
 

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-3'}),
        }
