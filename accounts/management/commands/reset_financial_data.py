"""
Wipes all financial/project data (Fund Sources, Fund Receipts,
Events, Budgets, Allocations, Expense Requests, Actual Event
Expenses, Documents, Audit Logs) WITHOUT touching Users or Profiles
-- so your team's logins (treasurer1, committee1, secretary, admin,
etc.) survive a reset.

Usage:
    python manage.py reset_financial_data
    python manage.py reset_financial_data --yes    (skip confirmation)

Deletion order matters: children are deleted before parents, since
most foreign keys here use on_delete=PROTECT (by design -- see the
models). Deleting an Event before its EventExpenses, for example,
would raise a ProtectedError.

The whole reset runs inside one database transaction, so if anything
fails part-way, NOTHING is deleted -- you never end up with a
half-wiped database.
"""

import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction


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
        from budgets.models import Allocation, Budget, Event, EventExpense
        from funds.models import FundReceipt, FundSource

        if not options["yes"]:
            confirm = input(
                "This will permanently delete ALL fund sources, receipts, events, "
                "budgets, allocations, expense requests, actual event expenses, "
                "documents, and audit logs.\n"
                "User accounts and roles will NOT be touched.\n"
                "Type 'yes' to continue: "
            )
            if confirm.strip().lower() != "yes":
                self.stdout.write(self.style.WARNING("Cancelled. Nothing was deleted."))
                return

        # Leaves first, roots last. Order here is the dependency order.
        steps = [
            ("Documents", Document),
            ("Audit log entries", AuditLog),
            ("Expense requests", ExpenseRequest),
            ("Actual event expenses", EventExpense),
            ("Allocations", Allocation),
            ("Budgets", Budget),
            ("Events", Event),
            ("Fund receipts", FundReceipt),
            ("Fund sources", FundSource),
        ]

        counts = {}
        with transaction.atomic():
            for label, model in steps:
                counts[label] = model.objects.count()
                model.objects.all().delete()

        # Only touch uploaded files AFTER the database part succeeded.
        for folder in ("documents", "expense_bills"):
            path = settings.MEDIA_ROOT / folder
            if path.exists():
                shutil.rmtree(path)

        self.stdout.write(self.style.SUCCESS("Financial/project data cleared:"))
        for label, _ in steps:
            self.stdout.write(f"  {label + ':':<24}{counts[label]}")
        self.stdout.write(self.style.SUCCESS("User accounts and roles were NOT touched."))
