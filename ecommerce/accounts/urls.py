from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('verify-otp/', views.otp_verify_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password-otp/', views.reset_password_otp_view, name='reset_password_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),

    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Address URLs
    path('add-address/', views.add_address, name='add_address'),
    path('update-address/<int:id>/', views.update_address_view, name='update_address'), 
    path('delete-address/<int:id>/', views.delete_address, name='delete_address'),
    
    path('wallet/', views.wallet_view, name='wallet_view'),
    path('wallet-payment/', views.wallet_payment, name='wallet_payment'),
    path('contact/', views.contact_view, name='contact'),
]