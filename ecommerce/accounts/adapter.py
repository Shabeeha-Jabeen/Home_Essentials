# accounts/adapter.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    # Redirect after successful login/signup
    def get_login_redirect_url(self, request):
        # Change 'home' to your home URL name
        return reverse('home')

    # Redirect on social login error instead of showing failure page
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        # Optional: Add a message if you want
        from django.contrib import messages
        messages.error(request, "Social login failed. Please try again.")
        return redirect('login')
