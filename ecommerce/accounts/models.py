from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone  
from datetime import timedelta
from django.urls import reverse 
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.code}"

    
    def is_expired(self):
        return timezone.now() > (self.created_at + timedelta(seconds=120))

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Address(models.Model):
    ADDRESS_CHOICES = (
        ('Home', 'Home'),
        ('Office', 'Office'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    street_address = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, null=True) 
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - ₹{self.balance}"

class WalletTransaction(models.Model):
    TRANSACTION_TYPE = (
        ('CREDIT', 'Credit'), 
        ('DEBIT', 'Debit'),  
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"    