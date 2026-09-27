# ANAA Fund Management System - Iteration 1 (Authentication & Roles)

This is the starting Django project for the ANAA Fund Management,
Allocation, Approval, Audit & Transparency System, covering
**Iteration 1: Authentication & Roles** from the project schedule.

## What's implemented

- `accounts` app with a `Profile` model extending Django's built-in
  `User`, carrying a `role` field (Treasurer/Admin, Committee/Approver,
  Member/Requester)
- A signal that auto-creates a Profile (default role: Member/Requester)
  whenever a new User is created
- Login / logout using Django's built-in authentication (no custom
  password handling -- Django's PBKDF2 hashing is used automatically)
- A `role_required` decorator in `accounts/decorators.py` for
  protecting views by role (use this on every module you build next)
- A role-aware dashboard that shows different quick-action cards
  depending on the logged-in user's role
- Django admin registered for managing Profiles/roles
- Tailwind CSS via CDN for styling (no build step needed)

## Setup (Windows / VS Code)

1. Open this folder in VS Code.
2. Open a terminal (`` Ctrl+` ``) and create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
   (macOS/Linux: `source venv/bin/activate`)
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Press `Ctrl+Shift+P` -> "Python: Select Interpreter" -> choose the
   one inside your new `venv` folder.
5. Run migrations (already applied once for you, but run again after
   pulling changes or resetting the DB):
   ```
   python manage.py migrate
   ```
6. Start the dev server:
   ```
   python manage.py runserver
   ```
7. Visit http://127.0.0.1:8000/ -- it redirects to the login page.

## Test accounts (already seeded in db.sqlite3)

| Username     | Password      | Role                  |
|--------------|---------------|------------------------|
| treasurer1   | testpass123   | Treasurer / Admin      |
| admin        | adminpass123  | Member/Requester + Django superuser (use /admin/ to change role) |

To create more test users with specific roles quickly, use the Django
shell:
```
python manage.py shell
```
```python
from django.contrib.auth.models import User
from accounts.models import Profile
u = User.objects.create_user('committee1', password='testpass123')
u.profile.role = Profile.ROLE_COMMITTEE_APPROVER
u.profile.save()
```

Or simpler: go to `/admin/`, log in as `admin`, and change any user's
role directly from the Profile admin page.

## Switching to MySQL later

Right now this uses SQLite for easy local development (per the
setup guidance you were given -- switch once your schema stabilizes).
When ready, in `anaa_system/settings.py` replace the `DATABASES`
block with:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'anaa_db',
        'USER': 'your_mysql_user',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```
Install the MySQL driver first: `pip install mysqlclient`, and create
the `anaa_db` database in MySQL Workbench/phpMyAdmin before running
`python manage.py migrate` again. Better yet, keep the DB credentials
out of settings.py entirely -- use `python-decouple` and a `.env` file
(excluded from Git) as discussed earlier.

## Next steps (Iteration 2 onward)

This project only has the `accounts` app so far. For Iteration 2
(Fund Management), create a new app:
```
python manage.py startapp funds
```
Add `'funds'` to `INSTALLED_APPS` in `settings.py`, then build the
`FundSource` and `FundReceipt` models per the ERD, protecting the
views with `@role_required(Profile.ROLE_TREASURER_ADMIN)` from
`accounts/decorators.py`.

## Security practices already in place

- Passwords: Django's default PBKDF2 hashing (never handled manually)
- CSRF: `{% csrf_token %}` used in the login form
- SQL injection: all queries go through the Django ORM
- Access control: `role_required` decorator enforces role checks
  server-side, not just hidden buttons in templates
- Secrets: none hardcoded yet -- add a `.env` file before deploying
  or committing to a public GitHub repo
