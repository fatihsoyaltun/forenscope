# ForenScope — Windows Server Production Setup

Target: Windows Server 2019/2022, LAN-only, no Docker.

---

## 1. Install Python 3.12

1. Download the Windows installer from https://python.org (Python 3.12.x, 64-bit).
2. Run the installer. Check **"Add Python to PATH"** and **"Install for all users"**.
3. Verify:
   ```
   python --version
   ```

---

## 2. Install PostgreSQL 16

1. Download the installer from https://www.postgresql.org/download/windows/.
2. During setup create a password for the `postgres` superuser.
3. After installation, open **pgAdmin** or **psql** and run:
   ```sql
   CREATE USER forenscope WITH PASSWORD 'strong_password_here';
   CREATE DATABASE forenscope_db OWNER forenscope;
   ```

---

## 3. Clone the repository

Open **Command Prompt** (run as Administrator):

```cmd
cd C:\
git clone <repo-url> forenscope
cd forenscope
```

If Git is not installed, download it from https://git-scm.com/download/win.

---

## 4. Create virtual environment

```cmd
python -m venv venv
call venv\Scripts\activate
```

---

## 5. Create the .env file

Copy `.env.example` to `.env` and fill in all values:

```cmd
copy .env.example .env
notepad .env
```

Key values to set:

| Variable | Example value |
|---|---|
| `DJANGO_SECRET_KEY` | A long random string (50+ chars) |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_ALLOWED_HOSTS` | `192.168.1.100,localhost` |
| `DB_PASSWORD` | Password you chose in step 2 |

Generate a secret key with:
```cmd
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 6. Install dependencies

```cmd
pip install -r requirements.txt
```

---

## 7. Apply database migrations

```cmd
python manage.py migrate
```

---

## 8. Create groups and lookup data

```cmd
python manage.py setup_groups
python manage.py setup_lookups
```

---

## 9. Create superuser

```cmd
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

---

## 10. Collect static files

```cmd
python manage.py collectstatic --noinput
```

Files are written to the path defined in `STATIC_ROOT` in `.env`.

---

## 11. Run the application

Use the provided batch file for day-to-day starts:

```cmd
deploy\start_windows.bat
```

Or manually:

```cmd
call venv\Scripts\activate
set DJANGO_SETTINGS_MODULE=config.settings.production
waitress-serve --port=8000 --threads=4 config.wsgi:application
```

The application will be available at `http://YOUR_SERVER_IP:8000`.

---

## 12. (Optional) Run as a Windows Service

To have ForenScope start automatically with Windows, use **NSSM** (Non-Sucking Service Manager):

1. Download NSSM from https://nssm.cc/download.
2. Open Command Prompt as Administrator:
   ```cmd
   nssm install ForenScope
   ```
3. In the NSSM GUI:
   - **Path**: `C:\forenscope\venv\Scripts\waitress-serve.exe`
   - **Arguments**: `--port=8000 --threads=4 config.wsgi:application`
   - **Startup directory**: `C:\forenscope`
4. Under the **Environment** tab add:
   ```
   DJANGO_SETTINGS_MODULE=config.settings.production
   ```
5. Click **Install service**, then start it:
   ```cmd
   nssm start ForenScope
   ```

---

## 13. Firewall

Allow inbound traffic on port 8000 from LAN only:

```cmd
netsh advfirewall firewall add rule name="ForenScope" dir=in action=allow protocol=TCP localport=8000 remoteip=192.168.0.0/16
```

Adjust the `remoteip` subnet to match your LAN.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Make sure the venv is activated before running any `python` command |
| Database connection refused | Check PostgreSQL service is running; verify credentials in `.env` |
| Static files 404 | Re-run `collectstatic`; check `STATIC_ROOT` path in `.env` |
| `DisallowedHost` error | Add your server IP/hostname to `DJANGO_ALLOWED_HOSTS` in `.env` |
