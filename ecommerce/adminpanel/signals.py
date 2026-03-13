from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from accounts.models import UserProfile, Wallet

@receiver(post_save, sender=User)
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        Wallet.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
