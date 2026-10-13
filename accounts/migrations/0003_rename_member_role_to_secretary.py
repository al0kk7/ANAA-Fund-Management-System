"""
Data migration: the old "member_requester" role becomes "secretary".

The schema migration before this one only changed the allowed
choices/default -- it does not touch rows that already exist. Without
this step, every existing Member/Requester profile would keep the old
value, which no code recognises any more, and those users would
silently lose all their permissions (including the ability to submit
requests and record expenses).

Reversible: migrating back turns "secretary" into "member_requester"
again.
"""

from django.db import migrations

OLD = "member_requester"
NEW = "secretary"


def member_to_secretary(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")
    Profile.objects.filter(role=OLD).update(role=NEW)


def secretary_to_member(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")
    Profile.objects.filter(role=NEW).update(role=OLD)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_profile_role"),
    ]

    operations = [
        migrations.RunPython(member_to_secretary, secretary_to_member),
    ]
