# Spesifikasi SMKRE

**Sistema Monitorizasaun Konflitu Rai no Eviksaun — Rede ba Rai**
Dokumen acuan tim (Onosio, Ricardo, Olavio). Berisi semua keputusan hasil diskusi dengan pemilik sistem.
Jika ada perubahan keputusan, perbarui dokumen ini di commit yang sama.

---

## 1. Tujuan dan konteks

- Dipakai oleh **Rede ba Rai** (redebarai.org) untuk **input data dan analisis** kasus konflik tanah dan penggusuran. Rede ba Rai bukan instansi yang memutuskan kasus.
- Alur: staf lapangan (Investigadór) → server pusat di Dili → sede (Admin, Analista) → tim hukum (Ofisiál Legál) → portal publik (tahap akhir).

## 2. Teknologi

| Aspek | Keputusan |
|---|---|
| Framework | Django 5.2 + DRF, proyek terpisah, repo privat `SMKRE` |
| Database | SQLite (dev) · PostgreSQL (produksi) |
| UI | **Bootstrap 4.6** (sama dengan proyek lama), Font Awesome 4.7, jQuery 3.7. **Semua aset lokal**, tanpa CDN. |
| Font | Montserrat (judul) + Lato (teks), lokal |
| Warna | Hijau `#82DA36`, teal `#16B78A` / `#0E8A68`, marun `#6B1E23` (dari logo), gelap `#222`, latar `#F1F2F1` |
| Bahasa | Tetun (default), Português, English, Bahasa Indonesia. Halaman offline: Tetun saja. Ganti bahasa lewat klik bendera di topbar. |
| Password | Argon2 |
| API offline | JWT (SimpleJWT). Refresh token berlaku 7 hari (= izin offline). |
| Background | Celery + Redis + Celery Beat. Di dev: `CELERY_ALWAYS_EAGER=True` (tanpa Redis). |
| Static | WhiteNoise |
| Email | Sementara Gmail `gomesriki12345@gmail.com` (App Password di `.env`), nanti email organisasi |
| Gaya kode | Mengikuti proyek sjdf/SGDS: function-based view, indentasi tab, context `group/page/title/legend`, crispy `Row/Column`, `@allowed_users`, `c_user_...` |

## 3. Role (RBAC) — `config/rbac.py`

| Role (Group) | Nama di dokumen | Hak akses |
|---|---|---|
| `superadmin` | Superadmin | Semua; membuat Admin; verifikasi; publikasi Policy Brief |
| `admin` | Admin | Kelola user (kecuali superadmin), reset password, verifikasi, **satu-satunya pemberi izin offline** |
| `analista` | Analista (Advocacy Coordinator) | Dashboard, hotspot, tren, laporan PDF/Excel, membuat Policy Brief |
| `ofisial_legal` | Ofisiál Legál (Legal Advisor) | Document Vault, tambah catatan/dokumen hukum, ubah status → Aksaun Legál |
| `investigador` | Investigadór (staf) | Input kasus di munisípiu tugasnya, bisa offline, hanya melihat kasusnya sendiri |

## 4. User dan keamanan akun

- Model mengikuti pola `Emp` + `EmpUser`: **`Pesoal`** + **`PesoalUser`**.
- **Username = email** (huruf kecil).
- Password default `redebarai@2026` disimpan di `.env` (`DEFAULT_PASSWORD`), **wajib diganti saat login pertama** dan tidak boleh dipakai lagi sebagai password baru.
- Reset oleh admin → kembali ke default + wajib ganti + token JWT dicabut. Lupa password → link email (berlaku 1 jam).
- Salah password 5× → akun dikunci 30 menit (django-axes).
- Menonaktifkan user → izin offline dan token langsung dicabut.

## 5. Izin offline

- Hanya **Admin** yang memberi. Berlaku **7 hari**, bisa diperpanjang atau dibatalkan.
- Habis → **tidak bisa membuat kasus baru, tetapi tetap bisa sinkron**.
- Celery Beat harian: menonaktifkan izin yang habis + pengingat 1 hari sebelumnya.
- HP: bebas, tetapi user harus diaktifkan admin. HP organisasi = Android (fitur penuh). iOS didukung (wajib *Add to Home Screen*, sinkron manual).
- **PIN SMKRE 6 digit** untuk membuka mode offline; PIN juga mengenkripsi data di HP (AES-256). Salah 5× → wajib login online. Lupa PIN → login online, data belum sinkron tidak hilang.

## 6. Status

**Status Dadus** (alur data):

| Kode | Label | Staf bisa edit? | Diubah oleh |
|---|---|---|---|
| `DRAFT` | Rascunho | Ya | Staf |
| `ONGOING` | Iha Terrenu (sudah ada foto awal/GPS) | Ya | Staf |
| `PENDING` | Hein Sinál (selesai, menunggu sinyal) | Ya | Staf |
| `SYNCED` | Hein Verifikasaun | Tidak | Otomatis saat sinkron |
| `VERIFIED` | Verifikadu | Tidak | Admin/Superadmin |
| `COMPLETED` | Remata (kompensasi sudah dibayar) | Tidak | Admin/Superadmin |
| `REJECTED` | Rejeitadu (bisa diperbaiki + sinkron ulang) | Ya | Admin/Superadmin (alasan wajib) |
| `CANCELED` | Kanseladu (palsu/duplikat, final) | Tidak | Admin/Superadmin (alasan wajib) |

**Status Kazu** (dokumen Anexu A): `ABERTU` → `INVESTIGASAUN` → `AKSAUN_LEGAL` → `TAKA`. Diubah Admin dan Ofisiál Legál.

Badge: satu file include `kazu/badge_status.html` dan `kazu/badge_status_kazu.html`. Tambahan badge **URJENTE** (marun).

**Verifikasi:** klik notifikasi 🔔 → detail kasus → tombol di bawah (Verifika / Rejeita / Kansela / Remata) → pop-up konfirmasi → notifikasi 🔔 + email ke staf pemilik kasus. Semua perubahan dicatat di riwayat (siapa, kapan, alasan).

## 7. Data kasus (Anexu A + Anexu E)

- **ID:** UUID dibuat di HP (anti-bentrok) + kode dari server saat sinkron: `SMKRE-<MUN>-<TAHUN>-<NOMOR>`.
- **Kazu:** judul, status dadus, status kazu, tanggal laporan, tanggal kejadian (≤ tanggal laporan), deskripsi, **tipe rai**, lokasi (munisípiu, postu, suku, aldeia, GPS), konsentimentu, urjente, observasaun, dibuat oleh.
- **Tipu konflitu:** Deslokamentu Forsadu · Konflitu Rai Tradisionál · Akizisaun Rai ba Projetu Dezenvolvimentu · Disputa Fronteira Rai · Seluk (wajib penjelasan).
- **Tipu rai:** Rai Estadu · Rai Privadu · Rai Tradisionál · Rai Disputa.
- **Uma-kain afetada:** uma-kain, total ema, mane, feto, labarik, katuas-ferik, ema ho defisiénsia (angka).
- **Insidente eviksaun** (banyak): tipe (Forsadu / Voluntáriu / Orden Tribunál), hari pemberitahuan, aparat keamanan hadir (ya/tidak), kerusakan, narasi.
- **Atór envolvidu** (banyak): Autoridade Governu · Polísia · Militár/F-FDTL · Empreza Privadu · Membru Komunidade · Seluk; nama; peran.
- **Estragu patrimóniu:** uma destruidu · rai agrikultura afetadu · to'os destruidu · fatin sagradu afetadu · estragu seluk.
- **Evidénsia:** foto maks. 5 (±1 MB, cap tanggal/jam/GPS), video maks. 1 (60 detik / 50 MB), dokumen legal, deklarasaun testemuña. **Kamera saja, tanpa galeri.** File hanya bisa dibuka lewat login.
- **Nesesidade urjente:** Apoiu Legál · Abrigu Emerjénsia · Apoiu Mediasaun · Asaun Advokasia → badge URJENTE + notifikasi prioritas.
- **Konsentimentu wajib** sebelum kasus disimpan.
- **Validasi:** field wajib; tanggal; GPS akurasi ≤ 50 m dan di dalam wilayah Timor-Leste (termasuk Oé-Cusse dan Ataúro); dropdown bertingkat standar.

## 8. Notifikasi

- Pola SGDS: `notification/api/` + `main/static/main/notif/notif_kazu.js` (polling setiap 30 detik).
- Kasus baru disinkron → Admin + Superadmin (🔔 + email). Perubahan status → staf pemilik (🔔 + email).

## 9. Dashboard, peta, laporan

- Pola `report/views` (`[obj, count]`) + `report/api` + `report/templates/chart/*.js` (Highcharts, lokal).
- Kartu: total kasus, eviksaun aktif, uma-kain afetadu, remata, urjente. Tabel per status/tipe/munisípiu/tahun/afetadu/staf.
- Grafik: per munisípiu, tipe, status, tren bulanan, afetadu (stacked).
- Peta: **A + B** — GeoJSON batas munisípiu dan suku disimpan lokal (selalu tampil) + lapisan OpenStreetMap otomatis saat online. Mode pin ⇄ hotspot.
- Batas wilayah: dibuat dari data terbuka HDX (OCHA), disederhanakan, lalu disesuaikan dengan 14 munisípiu terbaru. Perlu dicek ulang oleh Rede ba Rai.
- Export Excel/PDF (DataTables + server-side untuk laporan besar lewat Celery).

## 10. Portal Publik (tahap terakhir)

- Hanya kasus **Verified/Completed**, **anonim**: tanpa nama/kontak, tanpa foto wajah, tanpa GPS persis.
- Peta warna **per suku**. Suku dengan < 3 kasus ditampilkan sebagai "< 3". Admin bisa menandai kasus "la publika".
- Policy Brief: dibuat Analista, dipublikasikan Admin/Superadmin. Laporan masyarakat: cukup nomor kontak (tidak ada form publik).

## 11. Struktur folder

```
smkre/ main/ config/ custom/ users/ notification/      ← tahap 1 (selesai)
kazu/ sinkron/ report/ legal/ publiku/                 ← tahap berikutnya
locale/ logs/ media/ docs/ tools/ templates/
```

Semua nama folder huruf kecil (hindari `Api` vs `api` di server Linux).

## 12. Keamanan

CSP (tanpa inline script, pakai nonce), Permissions-Policy (kamera dan GPS hanya dari SMKRE), HSTS + HTTPS, cookie Secure/HttpOnly/SameSite, CSRF, X-Frame-Options, django-axes, media hanya lewat login, URL admin Django rahasia (`ADMIN_URL`), log keamanan di `logs/seguransa.log`.

## 13. Tahapan

1. ✅ Fondasi
2. Kasus + verifikasi + notifikasi
3. Dashboard, peta, laporan, export
4. Offline PWA (IndexedDB terenkripsi, PIN, GPS, kamera, sinkron)
5. Legal (Document Vault), uji coba, deploy
6. Portal Publik
