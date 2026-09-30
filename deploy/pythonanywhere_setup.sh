#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════
# SMKRE — setup otomátiku iha PythonAnywhere (seguru atu la'o dala barak)
#
# Iha PythonAnywhere → Consoles → Bash:
#   curl -fsSL https://raw.githubusercontent.com/Odoly23/SMKRE/main/deploy/pythonanywhere_setup.sh -o setup.sh && bash setup.sh
# ka (se kódigu iha ona):
#   bash ~/SMKRE/deploy/pythonanywhere_setup.sh
#
# Opsionál (la'o otomátiku tomak, inklui tab Web no Tasks):
#   Account → API token → Create. Konsole foun sei iha variavel $API_TOKEN.
# ══════════════════════════════════════════════════════════════════════
set -euo pipefail

U="${USER}"
DOMAIN="${U}.pythonanywhere.com"
APP="${HOME}/SMKRE"
VENV="${HOME}/.virtualenvs/smkre-env"
PY="${PY:-python3.11}"
REPO="${REPO:-https://github.com/Odoly23/SMKRE.git}"
WSGI="/var/www/${U}_pythonanywhere_com_wsgi.py"
API="https://www.pythonanywhere.com/api/v0/user/${U}"

pasu() { echo; echo "══════ $1"; }
ok()   { echo "  ✔ $1"; }

pasu "1/7 Kódigu husi GitHub"
if [ -d "${APP}/.git" ]; then
	git -C "${APP}" pull --ff-only origin main
else
	git clone "${REPO}" "${APP}"
fi
cd "${APP}"
ok "$(git log --oneline -1)"

pasu "2/7 Virtualenv (${PY}) no pakote"
[ -x "${VENV}/bin/python" ] || "${PY}" -m venv "${VENV}"
"${VENV}/bin/pip" install -q --upgrade pip
"${VENV}/bin/pip" install -q -r requirements.txt
ok "virtualenv: ${VENV}"
PYV="${VENV}/bin/python"

pasu "3/7 Konfigurasaun .env"
hakerek_env() {   # troka ka aumenta KEY=VALOR iha .env
	local key="$1" val="$2"
	if grep -q "^${key}=" .env; then sed -i "s|^${key}=.*|${key}=${val}|" .env; else echo "${key}=${val}" >> .env; fi
}
if [ ! -f .env ]; then
	cp .env.example .env
	hakerek_env SECRET_KEY "$(${PYV} -c 'import secrets;print(secrets.token_urlsafe(50))')"
	hakerek_env ADMIN_URL "jestaun-$(${PYV} -c 'import secrets;print(secrets.token_hex(4))')/"
	hakerek_env DEBUG False
	hakerek_env ALLOWED_HOSTS "${DOMAIN}"
	hakerek_env CSRF_TRUSTED_ORIGINS "https://${DOMAIN}"
	hakerek_env SITE_URL "https://${DOMAIN}"
	hakerek_env DB_ENGINE sqlite
	hakerek_env CELERY_ALWAYS_EAGER True
	hakerek_env USE_REDIS_CACHE False
	hakerek_env SECURE_SSL_REDIRECT False
	hakerek_env BEHIND_PROXY True
	hakerek_env CLIENT_IP_HEADER HTTP_X_REAL_IP
	hakerek_env EMAIL_BACKEND django.core.mail.backends.console.EmailBackend
	chmod 600 .env
	ok ".env kria (SECRET_KEY aleatóriu). Admin Django: https://${DOMAIN}/$(grep '^ADMIN_URL=' .env | cut -d= -f2)"
else
	ok ".env iha ona (la muda)"
fi

pasu "4/7 Base dadus, tradusaun no file statiku"
${PYV} manage.py migrate --noinput
${PYV} manage.py setup_smkre
${PYV} manage.py import_wilayah custom/data/wilayah/wilayah_dm31_2026.xlsx   # suku no aldeia (DM 31/2026)
${PYV} manage.py compile_lian
${PYV} manage.py collectstatic --noinput
${PYV} manage.py check --deploy || true
ok "base dadus prontu"

pasu "5/7 Superadmin"
if ${PYV} manage.py shell -c "from django.contrib.auth.models import User; import sys; sys.exit(0 if User.objects.filter(is_superuser=True).exists() else 1)"; then
	ok "Superadmin iha ona"
else
	EMAIL="${SMKRE_SUPERADMIN_EMAIL:-}"; NARAN="${SMKRE_SUPERADMIN_NARAN:-}"
	[ -n "${EMAIL}" ] || read -rp "  Email Superadmin: " EMAIL
	[ -n "${NARAN}" ] || read -rp "  Naran Superadmin: " NARAN
	if [ -n "${SMKRE_SUPERADMIN_PASSWORD:-}" ]; then
		${PYV} manage.py kria_superadmin --email "${EMAIL}" --naran "${NARAN}" --password "${SMKRE_SUPERADMIN_PASSWORD}"
	else
		echo "  Password (la hatudu iha ekran; minimu karakter 10, la'ós password default):"
		${PYV} manage.py kria_superadmin --email "${EMAIL}" --naran "${NARAN}"
	fi
fi

pasu "6/7 Web app (${DOMAIN})"
if [ -n "${API_TOKEN:-}" ]; then
	H="Authorization: Token ${API_TOKEN}"
	if [ "$(curl -s -o /dev/null -w '%{http_code}' -H "${H}" "${API}/webapps/${DOMAIN}/")" != "200" ]; then
		curl -s -H "${H}" -X POST "${API}/webapps/" -d "domain_name=${DOMAIN}" -d "python_version=python311" > /dev/null
		ok "Web app kria"
	fi
	sed "s|<username>|${U}|g" deploy/pythonanywhere_wsgi.py > "${WSGI}"
	ok "WSGI: ${WSGI}"
	curl -s -H "${H}" -X PATCH "${API}/webapps/${DOMAIN}/" -d "virtualenv_path=${VENV}" -d "force_https=true" > /dev/null
	ok "virtualenv + Force HTTPS"
	if ! curl -s -H "${H}" "${API}/webapps/${DOMAIN}/static_files/" | grep -q '"/static/"'; then
		curl -s -H "${H}" -X POST "${API}/webapps/${DOMAIN}/static_files/" -d "url=/static/" -d "path=${APP}/staticfiles" > /dev/null
	fi
	ok "static: /static/ → ${APP}/staticfiles"
	curl -s -H "${H}" -X POST "${API}/webapps/${DOMAIN}/reload/" > /dev/null
	ok "Reload"
else
	if [ -w "$(dirname "${WSGI}")" ] && [ -f "${WSGI}" ]; then
		sed "s|<username>|${U}|g" deploy/pythonanywhere_wsgi.py > "${WSGI}"
		ok "WSGI hakerek ona: ${WSGI}"
	fi
	cat <<EOF
  La iha \$API_TOKEN → halo iha tab Web (dala ida deit):
   1. Web → Add a new web app → Next → Manual configuration → Python 3.11
   2. Virtualenv  : ${VENV}
   3. WSGI file   : la'o fali script ne'e (sei hakerek WSGI automátiku)
                    ka kopia deploy/pythonanywhere_wsgi.py (troka <username> → ${U})
   4. Static files: URL /static/  →  ${APP}/staticfiles
   5. Force HTTPS : Enabled   →  klik Reload
EOF
fi

pasu "7/7 Knaar kada loron (06:00 Dili = 21:00 UTC)"
KMD="${VENV}/bin/python ${APP}/manage.py knaar_loron"
if [ -n "${API_TOKEN:-}" ]; then
	if ! curl -s -H "Authorization: Token ${API_TOKEN}" "${API}/schedule/" | grep -q "knaar_loron"; then
		curl -s -H "Authorization: Token ${API_TOKEN}" -X POST "${API}/schedule/" \
			-d "command=${KMD}" -d "enabled=true" -d "interval=daily" -d "hour=21" -d "minute=0" > /dev/null
	fi
	ok "Task: ${KMD}"
else
	echo "  Tasks → Daily 21:00 → ${KMD}"
fi

echo
echo "══════ PRONTU → https://${DOMAIN}/portal/  ·  https://${DOMAIN}/login/  ·  https://${DOMAIN}/sinkron/"
echo "Atualiza versaun foun iha futuru: bash ${APP}/deploy/pythonanywhere_setup.sh"
