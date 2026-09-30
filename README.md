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
report/         # dashboard, gráfiku (templates/chart/*.js), mapa (templates/maps/), lista, eksporta Excel — api/ + views/
sinkron/        # app offline Investigadór (/sinkron/) + API sinkron JWT (api/) — regra iha services.py
legal/          # Document Vault, nota/prazu legál, dossier imprime — regra iha services.py
publiku/        # portal públiku /portal/ (mapa + gráfiku interativu, publikasaun) — regra privasidade iha services.py
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
python manage.py setup_horariu  # knaar automátiku kada loron (Celery Beat)
python manage.py compile_lian   # tradusaun .po → .mo
python manage.py kria_superadmin --email ita@redebarai.org --naran "Naran Ita"
python manage.py kria_dadus_demo   # (opsionál, DEBUG deit) kazu [DEMO] ba teste dashboard/mapa
python manage.py runserver
```

Loke http://127.0.0.1:8000 → login ho email.

> **Redis la presiza** iha dev: `CELERY_ALWAYS_EAGER=True` iha `.env` halo knaar la'o kedas. Email hatudu iha terminal (console).

### Suku no Aldeia

Dadus ofisiál **Diploma Ministerial 31/2026** (472 suku, 2250 aldeia) prontu iha `custom/data/wilayah/`:

```bash
python manage.py import_wilayah custom/data/wilayah/wilayah_dm31_2026.xlsx --dry-run   # haree uluk
python manage.py import_wilayah custom/data/wilayah/wilayah_dm31_2026.xlsx
```

57 suku marka **VERIFIKA** (postu la klaru iha PDF): prenxe `postu_code` iha aba *Suku* no import fali. Detalla: `tools/wilayah_dm31/README.md`.


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

## 📱 App Offline (Investigadór)

1. Admin fó **autorizasaun offline** (loron 7) iha menu *Offline*.
2. Investigadór loke **`/sinkron/`** iha HP (Chrome Android / Safari iPhone, **HTTPS**) → login dala ida → kria **PIN númeru 6**.
3. Iha terrenu (la iha sinál): *Kazu Foun* → pasu 6 → GPS (≤ 50 m) → foto (máx. 5) / vídeo (60 s) husi kámera deit → konsentimentu → **Prontu**.
4. Bainhira iha sinál: sinkron automátiku (ka klik *Sinkron*). Kazu hetan kódigu `SMKRE-<MUN>-<TINAN>-<NÚMERU>` no Admin simu notifikasaun.

| Regra | Detalla |
|---|---|
| Enkriptasaun | Dadus kazu, foto, vídeo no token enkripta ho PIN (PBKDF2 310.000 + AES-256-GCM) iha IndexedDB |
| PIN sala dala 5 | Dadus iha HP hamoos automátiku |
| La uza minutu 5 | App xave, tenke tama PIN fali |
| Autorizasaun remata | Labele kria kazu foun; bele nafatin sinkron kazu ne'ebé kria durante autorizasaun (server verifika `kria_iha`) |
| Sinkron susesu | Dadus privadu hamoos husi HP; kódigu kazu deit mak hela |
| Koneksaun kotu | Koko fali la kria duplikadu (ID UUID husi HP) |

> **Teste lokál:** online → [`docs/TESTE_ONLINE.md`](docs/TESTE_ONLINE.md) (`teste_online` + `cek_kazu`) · offline/HP → [`docs/TESTE_OFFLINE.md`](docs/TESTE_OFFLINE.md) (`teste_offline` + `cek_sinkron`).
>
> **Teste iha HP durante dev:** kámera, GPS no WebCrypto presiza **HTTPS** (ka `localhost`). `http://192.168.x.x` sei la servisu.

API: `POST /api/auth/token/` · `GET /api/sinkron/opsaun/` · `GET|POST /api/sinkron/kazu/` · `POST /api/sinkron/kazu/<id>/evidensia/` · `POST /api/sinkron/kazu/<id>/haruka/`

## ⚖️ Legál (Document Vault)

- **Ofisiál Legál / Superadmin:** upload dokumentu (PDF, JPG, PNG, DOCX ≤ 20 MB), versaun foun, arkivu (ho razaun), nota no prazu.
- **Admin / Analista:** haree no download (dokumentu **konfidensiál** la mosu).
- Kazu tenke **verifika uluk**. Status kazu → *Aksaun Legál* = notifikasaun ba equipa legál.
- Kada file: tipu verifika tuir konteúdu, **SHA-256** rai, kada upload/download **rejista** (se, bainhira, IP). File la iha `/media/` — download liuhusi login deit.
- Prazu / audiénsia: lembrete automátiku loron 3 antes (`legal.tasks.lembra_prazu`, 07:00).
- **Dossier (PDF):** pájina A4 ho kop Rede ba Rai → *Imprime / Rai PDF*.
- Auditoria: `python manage.py verifika_vault` (kalkula fali SHA-256 file hotu).

## 🌍 Portal Públiku (`/portal/`)

- Topbar: kontaktu (telefone, fatin, email) iha karuk · bandeira lian iha los. Muda kontaktu iha `.env`: `PORTAL_TELEFONE`, `PORTAL_EMAIL`, `PORTAL_ENDERESU`.
- Mapa munisípiu + gráfiku barra (munisípiu, tipu konflitu, tinan, populasaun afetada). **Klik barra ka mapa → filtru ba hotu**; klik fali = hamoos. Link ho filtru bele fahe (URL).
- **Privasidade:** kazu **aprovadu** (Superadmin) ho konsentimentu deit, la'ós "la publika"; agregadu deit (la iha naran, foto, GPS); númeru 1–2 → **"< 3"**; populasaun afetada ba grupu ho kazu ≥ 3 deit. Regra iha `publiku/services.py`.
- **Publikasaun:** Analista (ka Admin) kria policy brief PDF → Admin / Superadmin **Publika** (menu *Publikasaun*).

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

> Uji coba online gratis: [`docs/DEPLOY_PYTHONANYWHERE.md`](docs/DEPLOY_PYTHONANYWHERE.md) · Server rasik: `docs/DEPLOY.md`

Haree **[docs/DEPLOY.md](docs/DEPLOY.md)** (PostgreSQL, Gunicorn, Nginx, Celery, Redis, HTTPS).

## 🗺️ Faze dezenvolvimentu

- [x] **Faze 1** — Fundasaun: estrutura, settings, RBAC, utilizador, password/email, autorizasaun offline, JWT, notifikasaun, layout mobile first, lian 4
- [x] **Faze 2** — Kazu: formuláriu, status rua, **Verifika (Admin) → Aprova (Superadmin)**, istória, evidénsia, notifikasaun
- [x] **Faze 3** — Dashboard, gráfiku, mapa hotspot/pin (GeoJSON lokál + OSM), lista DataTables, eksporta Excel (openpyxl) / PDF
- [x] **Faze 4** — Offline PWA: IndexedDB enkriptadu (PIN AES-256), formuláriu pasu 6, GPS ≤ 50 m, kámera deit, sinkron idempotente
- [x] **Faze 5** — Legál: Document Vault (SHA-256, versaun, rejistu asesu), nota + lembrete prazu, dossier PDF; prontu ba deploy
- [x] **Faze 6** — Portal Públiku: mapa + gráfiku interativu (filtru krúzadu), dadus anónimu ("< 3"), publikasaun, 4 lian
