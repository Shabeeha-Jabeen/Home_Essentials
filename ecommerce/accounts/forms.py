from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError

# --- PROFILE FORM ---
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-3'}),
        }

# --- SIGNUP FORM ---
class SignupForm(forms.Form):
    username = forms.CharField(label="Full Name", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match!")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email, is_active=True).exists():
            raise ValidationError("A user with this email already exists.")
        return email

# --- PASSWORD RESET FORMS ---
class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter registered email'}))

class ResetPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError("Passwords do not match!")
        return cleaned_data

# --- OTP & LOGIN ---
class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': '000000', 'type': 'number'}))

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))