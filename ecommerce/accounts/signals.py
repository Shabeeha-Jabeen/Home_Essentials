from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Wallet

# --- PROFILE & WALLET CREATION ---
@receiver(post_save, sender=User)
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        Wallet.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        
        UserProfile.objects.create(user=instance)
    
   
    if hasattr(instance, 'wallet'):
        instance.wallet.save()
    else:
        Wallet.objects.create(user=instance)