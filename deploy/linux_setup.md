# ForenScope — Ubuntu 24.04 LTS Production Setup

Target: Ubuntu 24.04 LTS, LAN-only, Gunicorn + Nginx + systemd.

---

## 1. System packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3.12-dev \
    postgresql-16 nginx git libmagic1 build-essential
```

---

## 2. PostgreSQL

```bash
sudo -u postgres psql <<EOF
CREATE USER forenscope WITH PASSWORD 'strong_password_here';
CREATE DATABASE forenscope_db OWNER forenscope;
EOF
```

---

## 3. Application user and directory

```bash
sudo useradd --system --shell /bin/bash --home /opt/forenscope forenscope
sudo mkdir -p /opt/forenscope
sudo git clone <repo-url> /opt/forenscope
sudo chown -R forenscope:www-data /opt/forenscope
```

---

## 4. Virtual environment and dependencies

```bash
sudo -u forenscope python3.12 -m venv /opt/forenscope/venv
sudo -u forenscope /opt/forenscope/venv/bin/pip install -r /opt/forenscope/requirements.txt
```

---

## 5. Environment file

```bash
sudo -u forenscope cp /opt/forenscope/.env.example /opt/forenscope/.env
sudo -u forenscope nano /opt/forenscope/.env
```

Key values to set:

| Variable | Value |
|---|---|
| `DJANGO_SECRET_KEY` | Generate with step below |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_ALLOWED_HOSTS` | `forenscope.local,YOUR_SERVER_IP` |
| `DB_PASSWORD` | Password from step 2 |
| `MEDIA_ROOT` | `/opt/forenscope/media` |
| `STATIC_ROOT` | `/opt/forenscope/staticfiles` |

Generate secret key:
```bash
/opt/forenscope/venv/bin/python -c \
  "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 6. Bootstrap

```bash
cd /opt/forenscope
sudo -u forenscope venv/bin/python manage.py migrate
sudo -u forenscope venv/bin/python manage.py setup_groups
sudo -u forenscope venv/bin/python manage.py setup_lookups
sudo -u forenscope venv/bin/python manage.py createsuperuser
sudo -u forenscope venv/bin/python manage.py collectstatic --noinput
```

Create required directories:
```bash
sudo -u forenscope mkdir -p /opt/forenscope/logs /opt/forenscope/media
sudo chmod 750 /opt/forenscope/logs /opt/forenscope/media
```

---

## 7. Systemd service

```bash
sudo cp /opt/forenscope/deploy/forenscope.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now forenscope
sudo systemctl status forenscope
```

---

## 8. Nginx

Generate a self-signed certificate for LAN use:
```bash
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
    -keyout /etc/ssl/private/forenscope.key \
    -out /etc/ssl/certs/forenscope.crt \
    -subj "/CN=forenscope.local"
```

Install the site config:
```bash
sudo cp /opt/forenscope/deploy/nginx.conf /etc/nginx/sites-available/forenscope
sudo ln -s /etc/nginx/sites-available/forenscope /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

---

## 9. Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 10. Automated backups

```bash
sudo chmod +x /opt/forenscope/deploy/backup.sh
# Run daily at 02:00
echo "0 2 * * * forenscope /opt/forenscope/deploy/backup.sh" \
    | sudo tee /etc/cron.d/forenscope-backup
```

---

## Verify

```bash
cd /opt/forenscope
sudo -u forenscope venv/bin/python manage.py check --deploy
curl -k https://forenscope.local/
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Gunicorn not starting | `journalctl -u forenscope -n 50` |
| 502 Bad Gateway | Check gunicorn is running: `systemctl status forenscope` |
| Static files missing | Re-run `collectstatic`; verify `STATIC_ROOT` in `.env` |
| Media files 403 | Check `nginx.conf` `internal` directive and file ownership |
| DB connection refused | `systemctl status postgresql`; verify `.env` credentials |
