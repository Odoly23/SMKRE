# Deploy SMKRE iha Server (Ubuntu 22.04 / 24.04)

> Pasu sira ne'e ezemplu. Adapta domain, utilizador no path tuir server Rede ba Rai.

## 1. Pakote sistema

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev postgresql redis-server nginx gettext certbot python3-certbot-nginx
```

## 2. PostgreSQL

```bash
sudo -u postgres psql
CREATE DATABASE smkre;
CREATE USER smkre WITH PASSWORD 'password-forte-ida';
ALTER ROLE smkre SET client_encoding TO 'utf8';
ALTER ROLE smkre SET timezone TO 'Asia/Dili';
GRANT ALL PRIVILEGES ON DATABASE smkre TO smkre;
ALTER DATABASE smkre OWNER TO smkre;
\q
```

## 3. Kódigu no `.env`

```bash
sudo mkdir -p /srv/smkre && sudo chown $USER /srv/smkre
git clone <url-repo> /srv/smkre && cd /srv/smkre
python3 -m venv Env && source Env/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Muda iha `.env`:

```
SECRET_KEY=<python -c "import secrets;print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=smkre.redebarai.org
CSRF_TRUSTED_ORIGINS=https://smkre.redebarai.org
SITE_URL=https://smkre.redebarai.org
DB_ENGINE=postgresql
DB_PASSWORD=password-forte-ida
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=<App Password Gmail>
DEFAULT_FROM_EMAIL=SMKRE Rede ba Rai <...>
CELERY_ALWAYS_EAGER=False
USE_REDIS_CACHE=True
ADMIN_URL=<url-segredu>/
```

```bash
python manage.py migrate
python manage.py setup_smkre
python manage.py compile_lian
python manage.py collectstatic --noinput
python manage.py kria_superadmin --email ... --naran "..."
python manage.py check --deploy
```

## 4. Gunicorn (systemd) — `/etc/systemd/system/smkre.service`

```ini
[Unit]
Description=SMKRE Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/smkre
ExecStart=/srv/smkre/Env/bin/gunicorn smkre.wsgi:application --workers 3 --bind unix:/run/smkre.sock --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

## 5. Celery worker + beat

`/etc/systemd/system/smkre-celery.service`

```ini
[Service]
User=www-data
WorkingDirectory=/srv/smkre
ExecStart=/srv/smkre/Env/bin/celery -A smkre worker -l info
Restart=always
```

`/etc/systemd/system/smkre-beat.service`

```ini
[Service]
User=www-data
WorkingDirectory=/srv/smkre
ExecStart=/srv/smkre/Env/bin/celery -A smkre beat -l info
Restart=always
```

Iha Django admin → *Periodic tasks*: aumenta `users.tasks.check_offline_permission` kada loron (ezemplu 06:00).

```bash
sudo chown -R www-data:www-data /srv/smkre/logs /srv/smkre/media
sudo systemctl daemon-reload
sudo systemctl enable --now smkre smkre-celery smkre-beat
```

## 6. Nginx — `/etc/nginx/sites-available/smkre`

```nginx
server {
    server_name smkre.redebarai.org;
    client_max_body_size 60M;          # vídeo máx. 50 MB

    location /static/ { alias /srv/smkre/staticfiles/; expires 30d; }
    # /media/ LA serve direta — foto no dokumentu liuhusi Django (login) deit

    location / {
        proxy_pass http://unix:/run/smkre.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/smkre /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d smkre.redebarai.org      # HTTPS obrigatóriu (GPS + kamera presiza HTTPS)
```

## 7. Backup kada loron (cron)

```bash
0 2 * * * pg_dump -U smkre smkre | gzip > /srv/backup/smkre-$(date +\%F).sql.gz
0 3 * * * tar czf /srv/backup/media-$(date +\%F).tgz -C /srv/smkre media
```

Rai backup mós iha fatin seluk (la'ós server hanesan).

## 8. Atualiza versaun

```bash
cd /srv/smkre && git pull
source Env/bin/activate && pip install -r requirements.txt
python manage.py migrate && python manage.py compile_lian && python manage.py collectstatic --noinput
sudo systemctl restart smkre smkre-celery smkre-beat
```
