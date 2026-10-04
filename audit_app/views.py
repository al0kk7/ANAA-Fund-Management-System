from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import AuditLog


@login_required
def audit_list(request):
    """
    Transparency by design: every logged-in user can view the audit
    trail, read-only -- matches the project's role table, where even
    Member/Requester has read-only visibility into audit logs.
    """
    logs = AuditLog.objects.select_related("user").all()[:200]
    return render(request, "audit_app/audit_list.html", {"logs": logs})
