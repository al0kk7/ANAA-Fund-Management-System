from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """
    Extends Django's built-in User with an ANAA-specific role.
    Three consolidated roles, per the approved project design:
      - treasurer_admin   : Treasurer/Admin (User 1)
      - committee_approver: Committee/Approver (User 2)
      - member_requester  : Member/Requester (User 3)
    """

    ROLE_TREASURER_ADMIN = "treasurer_admin"
    ROLE_COMMITTEE_APPROVER = "committee_approver"
    ROLE_MEMBER_REQUESTER = "member_requester"

    ROLE_CHOICES = [
        (ROLE_TREASURER_ADMIN, "Treasurer / Admin"),
        (ROLE_COMMITTEE_APPROVER, "Committee / Approver"),
        (ROLE_MEMBER_REQUESTER, "Member / Requester"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_MEMBER_REQUESTER)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    # Convenience checks used throughout the app instead of
    # scattering role-string comparisons everywhere.
    def is_treasurer_admin(self):
        return self.role == self.ROLE_TREASURER_ADMIN

    def is_committee_approver(self):
        return self.role == self.ROLE_COMMITTEE_APPROVER

    def is_member_requester(self):
        return self.role == self.ROLE_MEMBER_REQUESTER
