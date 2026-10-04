"""
log_action() is the single write-through logger called from every
state-changing view across the project (funds, budgets,
requests_app). Keeping all audit writes behind one small function,
rather than constructing AuditLog objects inline everywhere, means
the log format stays consistent and is easy to point to as "the"
audit mechanism when explaining the system.

Usage, from any view:

    from audit_app.utils import log_action
    log_action(request.user, "created", fund_receipt, description=f"NPR {fund_receipt.amount}")
"""

from .models import AuditLog


def log_action(user, action, target, description=""):
    AuditLog.objects.create(
        user=user,
        action=action,
        target_type=target.__class__.__name__,
        target_id=getattr(target, "pk", None),
        description=description or str(target),
    )
