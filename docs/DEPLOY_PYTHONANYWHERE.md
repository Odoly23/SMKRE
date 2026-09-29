# Deploy SMKRE ke PythonAnywhere (uji coba)

Hasil: SMKRE online di **https://&lt;username&gt;.pythonanywhere.com** dengan HTTPS gratis,
jadi app offline (`/sinkron/`) bisa dites di **HP sungguhan, Android dan iPhone**.

> Ganti `<username>` dengan username PythonAnywhere Anda di semua langkah.
> Untuk produksi resmi tetap disarankan server sendiri (PostgreSQL + Redis + Celery) — lihat `docs/DEPLOY.md`.

## ⚡ Cara cepat: satu script (disarankan)

Untuk akun **redebarai** hasilnya: **https://redebarai.pythonanywhere.com**

1. (Opsional, agar tab Web & Tasks ikut otomatis) **Account → API token → Create a new API token**.
   Token otomatis tersedia di console baru sebagai `$API_TOKEN` — tidak perlu disalin ke mana pun.
2. **Consoles → Bash** (buka console *baru* setelah membuat token), jalankan:
   ```bash
   git clone https://github.com/Odoly23/SMKRE.git
   bash SMKRE/deploy/pythonanywhere_setup.sh
   ```
3. Script meminta **email, nama dan password Superadmin** (password tidak tampil di layar).
4. Tanpa API token: ikuti 5 langkah tab **Web** yang dicetak di akhir script, lalu jalankan script sekali lagi (menulis file WSGI) dan klik **Reload**.

Script aman dijalankan berulang — juga dipakai untuk **update versi**: `bash ~/SMKRE/deploy/pythonanywhere_setup.sh`
(`.env` dan Superadmin yang sudah ada tidak diubah). Tanpa API token, setelah update klik **Reload** di tab Web.

Langkah manual lengkap (jika ingin memahami tiap langkah) ada di bawah.

## Batasan akun gratis (Beginner)

| Hal | Di akun gratis | Dampak di SMKRE |
|---|---|---|
| Domain | `<username>.pythonanywhere.com` + HTTPS | ✅ cukup untuk uji coba |
| Database | SQLite atau MySQL | ✅ keduanya didukung (PostgreSQL berbayar) |
| Redis / Celery | tidak ada | ✅ `CELERY_ALWAYS_EAGER=True` + tugas harian lewat **Tasks** |
| Disk | ±512 MB | cukup untuk teste; foto/video menambah pemakaian |
| Koneksi keluar | dibatasi | email SMTP mungkin tidak jalan → email tercatat di log (console) |
| Masa aktif web app | harus diperpanjang berkala (tombol di tab **Web**) | login dan klik *Run until …* |

## 1. Buat akun dan buka Bash console

1. Daftar di https://www.pythonanywhere.com (Beginner / gratis).
2. Dashboard → **Consoles** → **Bash**.

## 2. Ambil kode dari GitHub

```bash
git clone https://github.com/Odoly23/SMKRE.git
cd SMKRE
```

Jika repo **private**: saat diminta, username = akun GitHub, password = **Personal Access Token**
(GitHub → Settings → Developer settings → Fine-grained token, akses *Contents: Read-only* ke repo SMKRE).
Jangan menempel token di URL clone.

## 3. Virtualenv dan paket

```bash
mkvirtualenv --python=python3.11 smkre-env
pip install -r requirements.txt
# hanya jika memakai MySQL:
# pip install mysqlclient
```

## 4. File `.env`

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"   # salin hasilnya untuk SECRET_KEY
nano .env
```

Isi/ubah baris berikut (sisanya biarkan):

```
SECRET_KEY=<hasil perintah di atas>
DEBUG=False
ALLOWED_HOSTS=<username>.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://<username>.pythonanywhere.com
SITE_URL=https://<username>.pythonanywhere.com
ADMIN_URL=<kata-rahasia>/

# Database: pilih SATU
DB_ENGINE=sqlite
# DB_ENGINE=mysql
# DB_NAME=<username>$smkre
# DB_USER=<username>
# DB_PASSWORD=<password MySQL dari tab Databases>
# DB_HOST=<username>.mysql.pythonanywhere-services.com

# Tanpa Redis/Celery
CELERY_ALWAYS_EAGER=True
USE_REDIS_CACHE=False

# HTTPS diurus PythonAnywhere ("Force HTTPS" di tab Web)
SECURE_SSL_REDIRECT=False
BEHIND_PROXY=True
CLIENT_IP_HEADER=HTTP_X_REAL_IP

# Email: console = email hanya tercatat di log. Ganti ke smtp jika akun mengizinkan.
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Portal (contoh — ganti dengan kontak asli)
PORTAL_TELEFONE=+670 0000 0000
PORTAL_EMAIL=email@exemplu.tl
PORTAL_ENDERESU=Dili, Timor-Leste
```

Simpan: `Ctrl+O`, `Enter`, `Ctrl+X`.

Jika memakai MySQL: tab **Databases** → buat password MySQL → buat database `smkre` (nama lengkapnya jadi `<username>$smkre`).

## 5. Siapkan database dan file statis

```bash
python manage.py migrate
python manage.py setup_smkre
python manage.py compile_lian
python manage.py collectstatic --noinput
python manage.py kria_superadmin --email ita@redebarai.org --naran "Naran Ita"
python manage.py check --deploy
```

`check --deploy` akan menampilkan **1 peringatan `security.W008`** (SECURE_SSL_REDIRECT). Itu normal di sini:
HTTPS dipaksa oleh PythonAnywhere (*Force HTTPS* di langkah 6), bukan oleh Django.

## 6. Buat Web app

Tab **Web** → **Add a new web app** → *Next* → **Manual configuration** (bukan "Django") → **Python 3.11**.

Lalu di halaman Web app:

| Bagian | Isi |
|---|---|
| **Virtualenv** | `/home/<username>/.virtualenvs/smkre-env` |
| **WSGI configuration file** | klik file-nya, hapus semua isi, tempel isi `deploy/pythonanywhere_wsgi.py` (ganti `<username>`), **Save** |
| **Static files** | URL `/static/` → Directory `/home/<username>/SMKRE/staticfiles` |
| **Force HTTPS** | **Enabled** |

Jangan buat mapping untuk `/media/` — foto, video dan dokumen hanya boleh dibuka lewat login (Django).

Klik tombol hijau **Reload**.

## 7. Tugas harian (pengganti Celery Beat)

Tab **Tasks** → *Scheduled tasks* → Daily, jam **21:00 UTC** (= 06:00 waktu Dili):

```
/home/<username>/.virtualenvs/smkre-env/bin/python /home/<username>/SMKRE/manage.py knaar_loron
```

`knaar_loron` = menonaktifkan izin offline yang habis + pengingat, dan pengingat tenggat legal.

## 8. Uji coba

| Alamat | Yang dicek |
|---|---|
| `https://<username>.pythonanywhere.com/portal/` | Portal publik (tanpa login) |
| `https://<username>.pythonanywhere.com/login/` | Login superadmin → buat akun Admin, Investigadór, dll (menu Utilizador) |
| `https://<username>.pythonanywhere.com/sinkron/` | **App offline di HP** — Admin beri izin offline dulu (menu *Offline*) |

Alur teste online dan offline sama seperti `docs/TESTE_ONLINE.md` dan `docs/TESTE_OFFLINE.md`,
tapi cek data lewat Bash console PythonAnywhere:

```bash
cd ~/SMKRE && workon smkre-env
python manage.py cek_kazu          # kasus web + HP
python manage.py cek_sinkron       # kasus dari HP
```

> `teste_online`, `teste_offline` dan `kria_dadus_demo` sengaja **tidak jalan** saat `DEBUG=False`.
> Buat akun teste lewat menu **Utilizador** (password default dikirim/tercatat di log email).

## 9. Update versi baru

```bash
cd ~/SMKRE && workon smkre-env
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py compile_lian
python manage.py collectstatic --noinput
```
Lalu tab **Web** → **Reload**.

## Masalah umum

| Gejala | Solusi |
|---|---|
| "Something went wrong" / error 500 | Tab **Web** → *Error log* (paling bawah). Biasanya `.env` salah ketik atau `ALLOWED_HOSTS` |
| Halaman tanpa CSS | Belum `collectstatic`, atau mapping `/static/` salah folder |
| "CSRF verification failed" saat login | `CSRF_TRUSTED_ORIGINS` harus `https://<username>.pythonanywhere.com` (dengan https) |
| Redirect terus-menerus | Pastikan `SECURE_SSL_REDIRECT=False` dan pakai *Force HTTPS* dari tab Web |
| Email tidak terkirim | Akun gratis membatasi koneksi keluar → email ada di *Server log*; untuk teste tidak masalah |
| Kamera / GPS tidak jalan di HP | Buka lewat **https://**; izinkan kamera & lokasi di browser |
| Web app berhenti | Akun gratis: tab Web → klik perpanjang (*Run until …*) |
