"""
Wipes all financial/project data (Fund Sources, Fund Receipts,
Events, Budgets, Allocations, Expense Requests, Documents, Audit
Logs) WITHOUT touching Users or Profiles -- so your team's logins
(treasurer1, committee1, member1, admin, etc.) survive a reset.

Usage:
    python manage.py reset_financial_data
    python manage.py reset_financial_data --yes    (skip confirmation)

Deletion order matters: children are deleted before parents, since
most foreign keys here use on_delete=PROTECT (by design -- see the
models). Deleting a Budget before its Allocations, for example,
would raise a ProtectedError.
"""

import shutil

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deletes all financial/project data, keeping Users and Profiles intact."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes", action="store_true",
            help="Skip the confirmation prompt."
        )

    def handle(self, *args, **options):
        from audit_app.models import Document, AuditLog
        from requests_app.models import ExpenseRequest
        from budgets.models import Allocation, Budget, Event
        from funds.models import FundReceipt, FundSource

        if not options["yes"]:
            confirm = input(
                "This will permanently delete ALL fund sources, receipts, events, "
                "budgets, allocations, expense requests, documents, and audit logs.\n"
                "User accounts and roles will NOT be touched.\n"
                "Type 'yes' to continue: "
            )
            if confirm.strip().lower() != "yes":
                self.stdout.write(self.style.WARNING("Cancelled. Nothing was deleted."))
                return

        # Delete in dependency order: leaves first, roots last.
        doc_count = Document.objects.count()
        Document.objects.all().delete()

        audit_count = AuditLog.objects.count()
        AuditLog.objects.all().delete()

        req_count = ExpenseRequest.objects.count()
        ExpenseRequest.objects.all().delete()

        alloc_count = Allocation.objects.count()
        Allocation.objects.all().delete()

        budget_count = Budget.objects.count()
        Budget.objects.all().delete()

        event_count = Event.objects.count()
        Event.objects.all().delete()

        receipt_count = FundReceipt.objects.count()
        FundReceipt.objects.all().delete()

        source_count = FundSource.objects.count()
        FundSource.objects.all().delete()

        # Also clear uploaded files from media/documents/, since the
        # Document rows pointing to them are now gone.
        media_docs_path = settings.MEDIA_ROOT / "documents"
        if media_docs_path.exists():
            shutil.rmtree(media_docs_path)

        self.stdout.write(self.style.SUCCESS("Financial/project data cleared:"))
        self.stdout.write(f"  Documents:        {doc_count}")
        self.stdout.write(f"  Audit log entries: {audit_count}")
        self.stdout.write(f"  Expense requests:  {req_count}")
        self.stdout.write(f"  Allocations:       {alloc_count}")
        self.stdout.write(f"  Budgets:           {budget_count}")
        self.stdout.write(f"  Events:            {event_count}")
        self.stdout.write(f"  Fund receipts:     {receipt_count}")
        self.stdout.write(f"  Fund sources:      {source_count}")
        self.stdout.write(self.style.SUCCESS("User accounts and roles were NOT touched."))
