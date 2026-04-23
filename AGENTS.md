# ForenScope — Codex Context File

## Project
Internal on-premise service ticket and knowledge base system for forensic camera devices.
No internet exposure. Company LAN only.

## Stack
- Django 5.2, Python 3.12, PostgreSQL 16
- HTMX (CDN) + Django Templates — no React, no SPA, no build step
- Tailwind CSS (CDN only)
- Gunicorn + Nginx + systemd — NO Docker
- Ubuntu 24.04 LTS

## App Structure
```
apps/core/        → dashboard
apps/accounts/    → CustomUser, roles, MFA
apps/service/     → tickets, devices, parts, attachments
apps/knowledge/   → knowledge base articles
templates/        → all HTML templates
deploy/           → nginx.conf, systemd service, backup script
```

## Roles (Django Groups)
- Admin: full access to everything
- Technician: manages own tickets, can create draft articles, NO delete permission
- ReadOnly: view only, no forms, no create

## Hard Rules
- NEVER store binary files in PostgreSQL — use FileField, store path only
- NEVER use runserver in production
- Technician group must NOT have any delete_ permissions
- Always run makemigrations + migrate after model changes
- Validate real MIME type with python-magic on file upload (not just extension)
- Serve files via Nginx X-Accel-Redirect — never expose /media/ directly
- LoginRequiredMixin on every view
- All forms must be CSRF protected

## Installed Packages
```
Django==5.2.*
psycopg2-binary==2.9.*
gunicorn==22.*
django-htmx==1.*
django-auditlog==3.*
django-simple-history==3.*
django-two-factor-auth==1.*
django-otp==1.*
django-axes==6.*
python-magic==0.4.*
Pillow==10.*
django-environ==0.11.*
whitenoise==6.*
```

## Do NOT Add Yet
MinIO, Celery, Redis, Keycloak, FFmpeg, React, Docker, Elasticsearch

## Commands
```bash
python manage.py check
python manage.py check --deploy
python manage.py makemigrations && python manage.py migrate
python manage.py setup_groups
python manage.py setup_lookups
python manage.py test
```

## Completed Phases
- [x] Phase 0: Project skeleton ✓
- [x] Phase 1: Service data models
- [ ] Phase 2: Views and forms
- [ ] Phase 3: Auth, permissions, MFA
- [ ] Phase 4: Knowledge base
- [ ] Phase 5: Dashboard with real data
- [ ] Phase 6: Production deploy