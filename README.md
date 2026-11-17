# Job Portal

A Django job portal with custom employer and job-seeker accounts, job listings,
and job applications.

## Setup (Windows PowerShell)

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Set local environment variables. Generate a fresh secret key and set it for
   this PowerShell session:

   ```powershell
   $env:DJANGO_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(50))"
   $env:DJANGO_DEBUG = "true"
   ```

4. Create the local database and start the development server:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

Open <http://127.0.0.1:8000/> in a browser. Create an account to use the portal.

## Tests

Set `DJANGO_SECRET_KEY` as above, then run:

```powershell
python manage.py test
```

## Security

The local database, virtual environments, and environment files are excluded
from version control. Never commit production secrets or a database containing
real user data. Set `DJANGO_DEBUG` to `false` and configure
`DJANGO_ALLOWED_HOSTS` for deployment.
