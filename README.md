# SMKRE — Sistema Monitorizasaun Konflitu Rai no Eviksaun

Sistema Django ba **Rede ba Rai** atu rekolla, verifika, analiza no jere dadus kazu konflitu rai, deslokamentu no eviksaun iha Timor-Leste.
Mobile first · offline ba Investigadór (PWA) · lian 4 (Tetun, Português, English, Bahasa Indonesia).

> Dezenvolve husi: **Onosio, Ricardo, Olavio**

---

## 🚀 Teknolojia

| Parte | Teknolojia |
|---|---|
| Backend | Python 3.11+, Django 5.2, Django REST Framework, SimpleJWT |
| Database | SQLite (dev) · PostgreSQL (production) |
| Frontend | Bootstrap 4.6, jQuery 3.7, Font Awesome 4.7 — **lokál hotu (offline)** |
| Seguransa | Argon2, RBAC, django-axes, CSP, HTTPS/HSTS |
| Knaar kotuk | Celery + Redis (+ Celery Beat) |
| Static | WhiteNoise |

## 📁 Estrutura Projetu

```bash
smkre/          # konfigurasaun projetu: settings (lee .env), urls, middleware, celery
main/           # layout, varanda, pájina erru, static (css, js, fonts, flags, pwa, notif)
config/         # rbac.py, decorators, menu, utils, tasks (email), context processor
custom/         # master data: Munisípiu, Postu, Suku, Aldeia, opsaun padronizadu
users/          # Pesoal + PesoalUser, konta, password, autorizasaun offline, API JWT
notification/   # notifikasaun 🔔 + email (api/ hanesan pola SGDS)
kazu/           # kazu: formuláriu, status, verifikasaun (Admin) + aprovasaun (Superadmin), evidénsia, istória
report/         # dashboard, gráfiku (templates/chart/*.js), mapa hotspot, lista, eksporta Excel — api/ + views/
locale/         # tradusaun: tet, pt, en, id
tools/          # extract_lian.py (ekstrai testu tradusaun)
docs/           # SPESIFIKASAUN.md, DEPLOY.md, manuál formasaun
logs/           # error.log, sinkron.log, seguransa.log (la tama git)
templates/      # override template third-party (crispy)
```

## 💻 Instala iha laptop (development)

```bash
git clone <url-repo> SMKRE && cd SMKRE
python3 -m venv Env && source Env/bin/activate      # Windows: Env\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # depois muda SECRET_KEY iha .env
python manage.py migrate
python manage.py setup_smkre    # role (5), opsaun padronizadu, 14 munisípiu, 65 postu
python manage.py compile_lian   # tradusaun .po → .mo
python manage.py kria_superadmin --email ita@redebarai.org --naran "Naran Ita"
python manage.py kria_dadus_demo   # (opsionál, DEBUG deit) kazu [DEMO] ba teste dashboard/mapa
python manage.py runserver
```

Loke http://127.0.0.1:8000 → login ho email.

> **Redis la presiza** iha dev: `CELERY_ALWAYS_EAGER=True` iha `.env` halo knaar la'o kedas. Email hatudu iha terminal (console).

### Suku no Aldeia

Munisípiu no Postu Administrativu tama automátiku. Suku (452) no Aldeia import husi CSV:

```bash
python manage.py import_wilayah dadus/suku_aldeia.csv
```

Formatu: haree `custom/data/wilayah_template.csv` (`postu_code,suku_code,suku,aldeia_code,aldeia,latitude,longitude`).
Kódigu postu iha `custom/data/postu.csv`.

## 👥 Papél (RBAC)

Regra hotu iha **`config/rbac.py`**. Atu muda asesu, muda lista iha ne'ebá deit.

| Papél | Asesu prinsipál |
|---|---|
| `superadmin` | Hotu · kria Admin |
| `admin` | Jere utilizadór · verifika kazu · **fó autorizasaun offline (loron 7)** |
| `analista` | Dashboard, mapa, relatóriu, Policy Brief |
| `ofisial_legal` | Document Vault, nota legál |
| `investigador` | Input kazu iha munisípiu knaar (offline) |

**Fluxu kazu:** Investigadór haruka → **Admin: Verifika** → **Superadmin: Aprova** → Remata. Rejeita / Kansela ho razaun. Regra iha `kazu/services.py`.

Uza iha view:

```python
@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
def PesoalList(request):
```

## 🌐 Lian

- Testu fonte iha kódigu mak **Tetun**. File hotu iha `locale/`: `tet/`, `pt/`, `en/`, `id/` (`LC_MESSAGES/django.po`).
- Atu hadia testu Tetun la muda kódigu: edita `msgstr` iha `locale/tet/LC_MESSAGES/django.po`.
- Aumenta testu foun → `python tools/extract_lian.py` → prenxe `msgstr` iha `locale/<pt|en|id>/LC_MESSAGES/django.po` → `python manage.py compile_lian`.

## ✅ Test

```bash
python manage.py test
```

## 🔧 Se iha erru

| Erru | Haree |
|---|---|
| Erru 500 | `logs/error.log` (file + liña) |
| Login / konta xave | `logs/seguransa.log` |
| Sinkron HP | `logs/sinkron.log` |
| Email la to'o | `.env` seksaun 9 (Gmail presiza **App Password**) |
| Konta xave (sala dala 5) | `python manage.py axes_reset_username <email>` |

Konfigurasaun hotu iha `smkre/settings.py`, fahe ba seksaun **1–12** ho naran.

## 📦 Production

Haree **[docs/DEPLOY.md](docs/DEPLOY.md)** (PostgreSQL, Gunicorn, Nginx, Celery, Redis, HTTPS).

## 🗺️ Faze dezenvolvimentu

- [x] **Faze 1** — Fundasaun: estrutura, settings, RBAC, utilizador, password/email, autorizasaun offline, JWT, notifikasaun, layout mobile first, lian 4
- [x] **Faze 2** — Kazu: formuláriu, status rua, **Verifika (Admin) → Aprova (Superadmin)**, istória, evidénsia, notifikasaun
- [x] **Faze 3** — Dashboard, gráfiku, mapa hotspot/pin (GeoJSON lokál + OSM), lista DataTables, eksporta Excel (openpyxl) / PDF
- [ ] **Faze 4** — Offline PWA: IndexedDB enkriptadu (PIN), GPS, kamera, sinkron
- [ ] **Faze 5** — Legál (Document Vault), test, deploy
- [ ] **Faze 6** — Portal Públiku (anónimu, tuir suku)
