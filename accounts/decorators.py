"""
Role-based access control for ANAA Fund Management System.

Usage on any view:

    from accounts.decorators import role_required
    from accounts.models import Profile

    @role_required(Profile.ROLE_TREASURER_ADMIN)
    def create_fund_receipt(request):
        ...

Enforcing this at the view level (not just hiding buttons in the
template) is deliberate: a hidden link is not a secured page.
"""

from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


def role_required(*allowed_roles):
    """
    Restricts a view to users whose Profile.role is in allowed_roles.
    Always combined with login_required, since an anonymous user has
    no profile to check.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            profile = getattr(request.user, "profile", None)
            if profile is None or profile.role not in allowed_roles:
                return HttpResponseForbidden(
                    "You do not have permission to access this page."
                )
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
