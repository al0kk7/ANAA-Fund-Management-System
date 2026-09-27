"""
Auto-creates a Profile whenever a new User is created, so that a
freshly created user (including one made via `createsuperuser` or
the Django admin) always has a role to check against instead of
crashing on a missing OneToOne relation.

Default role is Member/Requester -- a Treasurer/Admin should
explicitly upgrade a user's role via the admin panel after creation.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
