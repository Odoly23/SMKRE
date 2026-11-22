# Deploy SIBAR-RbR ke cPanel (redebarai.org)

Hasil: SIBAR-RbR online di **https://sibar.redebarai.org** (disarankan subdomain, supaya situs utama
redebarai.org tidak terganggu), dengan email sistem dari **noreply@redebarai.org**.

Keuntungan dibanding PythonAnywhere gratis: aplikasi dan server email ada di hosting yang sama, jadi
**SMTP tidak diblokir**, dan tidak ada batasan akses internet keluar.

> Ganti `<cpaneluser>` dengan username cPanel Anda di semua langkah.

## 0. Syarat hosting (cek dulu)

| Kebutuhan | Di cPanel | Cara cek |
|---|---|---|
| **Setup Python App** (Phusion Passenger) | Menu *Software → Setup Python App* | Kalau menu tidak ada, minta ke penyedia hosting |
| **Python 3.10 atau lebih baru** (Django 5.2) | Pilihan versi di Setup Python App | Pilih 3.11 kalau ada |
| **MariaDB ≥ 10.5** atau **MySQL ≥ 8.0.11** | *Databases → MySQL Databases* | Terminal: `mysql --version` |
| **Terminal / SSH** | *Advanced → Terminal* | Untuk menjalankan perintah `manage.py` |
| **Cron Jobs** | *Advanced → Cron Jobs* | Untuk tugas harian |

## 1. Subdomain + HTTPS
1. *Domains → Create A New Domain* (atau *Subdomains*): `sibar.redebarai.org`.
   Document root biarkan saja (mis. `/home/<cpaneluser>/sibar.redebarai.org`), **jangan** pakai folder kode.
2. *Security → SSL/TLS Status* → jalankan **AutoSSL** untuk `sibar.redebarai.org` (sertifikat gratis).

## 2. Database MySQL
*Databases → MySQL Database Wizard*:
1. Database: `sibar` → nama lengkap `<cpaneluser>_sibar`.
2. User: `sibar` → `<cpaneluser>_sibar`, password kuat (simpan untuk `.env`).
3. Beri **ALL PRIVILEGES** ke database itu.

## 3. Email noreply
*Email → Email Accounts → Create*: `noreply@redebarai.org`, password kuat (simpan untuk `.env`).
Pengaturan SMTP (dari *Connect Devices*): server `mail.redebarai.org`, port **465**, SSL.

## 4. Ambil kode
*Advanced → Terminal*:
```bash
cd ~
git clone https://github.com/Odoly23/SMKRE.git sibar
```
Kode ada di `/home/<cpaneluser>/sibar` (di luar `public_html`, jadi file `.env` tidak bisa dibuka dari web).

## 5. Setup Python App
*Software → Setup Python App → Create Application*:

| Kolom | Isi |
|---|---|
| Python version | 3.11 (atau ≥ 3.10) |
| Application root | `sibar` |
| Application URL | `sibar.redebarai.org` |
| Application startup file | `passenger_wsgi.py` |
| Application Entry point | `application` |

Klik **Create**. Di bagian atas halaman muncul perintah untuk masuk ke virtualenv, mirip:
```bash
source /home/<cpaneluser>/virtualenv/sibar/3.11/bin/activate && cd /home/<cpaneluser>/sibar
```
Salin perintah itu — dipakai setiap kali menjalankan `manage.py`.

## 6. Pasang dependensi
Di Terminal (setelah perintah `source ...` di atas):
```bash
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
```
Driver MySQL memakai **PyMySQL** (Python murni), jadi tidak perlu kompilasi `mysqlclient`.

## 7. File `.env`
```bash
cp .env.example .env
nano .env
```
Isi minimal (nilai rahasia **hanya** di file ini, jangan dikirim lewat chat/email):
```
SECRET_KEY=<acak, minimal 50 karakter: python -c "import secrets;print(secrets.token_urlsafe(64))">
DEBUG=False
ALLOWED_HOSTS=sibar.redebarai.org
CSRF_TRUSTED_ORIGINS=https://sibar.redebarai.org
SITE_URL=https://sibar.redebarai.org
ADMIN_URL=<alamat admin rahasia, mis. kontrol-xxxx/>

DB_ENGINE=mysql
DB_NAME=<cpaneluser>_sibar
DB_USER=<cpaneluser>_sibar
DB_PASSWORD=<password database>
DB_HOST=localhost
DB_PORT=3306

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.redebarai.org
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_USE_TLS=False
EMAIL_HOST_USER=noreply@redebarai.org
EMAIL_HOST_PASSWORD=<password noreply>
DEFAULT_FROM_EMAIL=SIBAR - RbR <noreply@redebarai.org>
EMAIL_REPLY_TO=info@redebarai.org

PORTAL_EMAIL=info@redebarai.org
MAPBOX_TOKEN=<token Mapbox, opsional>

CELERY_ALWAYS_EAGER=True
USE_REDIS_CACHE=False
CACHE_DIR=/home/<cpaneluser>/sibar_cache
SECURE_SSL_REDIRECT=True
BEHIND_PROXY=False
CLIENT_IP_HEADER=

LIMPEZA_HAHU=<tanggal deploy, YYYY-MM-DD>
LIMPEZA_ATIVU=True
```
Lalu: `mkdir -p ~/sibar_cache && chmod 600 .env`

Catatan:
- `CACHE_DIR`: Passenger menjalankan beberapa proses; cache di file membuat batas login per-IP dan
  cache dashboard berlaku sama untuk semua proses.
- `EMAIL_REPLY_TO`: orang yang membalas email sistem akan sampai ke `info@redebarai.org`.

## 8. Siapkan database dan data awal
```bash
python manage.py migrate --noinput
python manage.py setup_smkre
python manage.py import_wilayah custom/data/wilayah/wilayah_dm31_2026.xlsx
python manage.py compile_lian
python manage.py collectstatic --noinput --clear
python manage.py kria_superadmin --email <email-anda> --naran "<Nama Anda>"
python manage.py check --deploy
python manage.py cek_email <email-anda>
```
`cek_email` memeriksa email langkah demi langkah dan harus berakhir dengan **[6] OK**.

## 9. Restart dan cek
*Setup Python App* → klik **Restart** (atau `mkdir -p ~/sibar/tmp && touch ~/sibar/tmp/restart.txt`).
- `https://sibar.redebarai.org/` → landing publik.
- `https://sibar.redebarai.org/Tama-Lai/` → login staf.
- `https://sibar.redebarai.org/sinkron/` → app offline investigador.

## 10. Tugas harian (Cron Jobs)
*Advanced → Cron Jobs → Add New Cron Job*, sekali sehari (mis. **05:10**; jam mengikuti zona waktu
server — cek dengan `date` di Terminal):
```
/home/<cpaneluser>/virtualenv/sibar/3.11/bin/python /home/<cpaneluser>/sibar/manage.py knaar_loron >> /home/<cpaneluser>/sibar/logs/cron.log 2>&1
```
Isinya: menutup izin offline yang habis + pengingat, pengingat tenggat legal, dan pembersihan kasus
30 hari (kansela → hapus). Pratinjau pembersihan: `python manage.py limpeza_kazu --dry-run`.

## Update versi baru
```bash
source /home/<cpaneluser>/virtualenv/sibar/3.11/bin/activate && cd /home/<cpaneluser>/sibar
git pull origin main
pip install --no-cache-dir -r requirements.txt
python manage.py migrate --noinput
python manage.py compile_lian
python manage.py collectstatic --noinput --clear
mkdir -p tmp && touch tmp/restart.txt
```

## Backup (wajib, karena ada penghapusan otomatis)
- *Files → Backup* (atau *JetBackup*): unduh backup database `<cpaneluser>_sibar` dan folder `~/sibar/media/`
  secara rutin, minimal mingguan.
- Manual: `mysqldump -u <cpaneluser>_sibar -p <cpaneluser>_sibar > ~/backup-sibar-$(date +%F).sql`

## Jika ada masalah
| Gejala | Cek |
|---|---|
| Halaman "We're sorry, but something went wrong" / 500 | `~/sibar/logs/error.log` dan log Passenger (*Setup Python App* → stderr) |
| `DisallowedHost` | `ALLOWED_HOSTS` di `.env` |
| CSS/JS tidak muncul | `python manage.py collectstatic --noinput --clear` lalu restart |
| Email tidak terkirim | `python manage.py cek_email <email>` — lihat tahap yang **SALA** |
| Error koneksi database | nama DB/user harus diawali `<cpaneluser>_`, `DB_HOST=localhost` |
| Perubahan `.env` tidak berlaku | Restart aplikasi (langkah 9) |
