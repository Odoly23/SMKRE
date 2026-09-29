# Teste Fluxu Online di Lokal (laptop)

Tujuan: memastikan kasus yang diisi lewat **formulir web (online)** benar-benar masuk dan berjalan sampai **Dashboard** dan **Portal Publik**:

```
Investigador isi form → Haruka → 🔔 Admin → Verifika → 🔔 Superadmin → Aprova → Dashboard + Portal Publik
```

## A. Persiapan (sekali)

```bash
cd SMKRE
source Env/bin/activate            # Windows: Env\Scripts\activate
python manage.py migrate
python manage.py setup_smkre
python manage.py teste_online      # buat 3 akun teste (hanya jika DEBUG=True)
python manage.py runserver
```

Akun teste (password semua: `Teste#Online-2026`):

| Peran | Email |
|---|---|
| Investigadór (munisípiu Liquiçá) | `teste.investigador@redebarai.org` |
| Admin | `teste.admin@redebarai.org` |
| Superadmin | `teste.superadmin@redebarai.org` |

Opsi: `python manage.py teste_online --munisipiu DIL`. Jika munisípiu belum punya daftar suku, dibuat `[TESTE] Suku` supaya form bisa dikirim.

> Pakai **3 browser berbeda** (atau jendela *Incognito* / profil Chrome lain) supaya bisa login 3 akun sekaligus.

## B. Langkah teste

1. **Investigadór** → http://127.0.0.1:8000 → menu **Kazu Foun**:
   - Isi Postu → Suku (dropdown berurutan), klik **Foti GPS** (izinkan lokasi; jika akurasi laptop > 50 m pakai DevTools → *Sensors* → koordinat Timor-Leste, mis. -8.6121, 125.2107).
   - Isi tanggal akontesimentu, tipe konflik, deskripsi, uma-kain/mane/feto (mane + feto = total), centang **konsentimentu**.
   - Klik **Rai no Haruka ba Verifikasaun** → muncul *"Kazu SMKRE-LIQ-2026-xxxxx haruka ona"*.
2. **Admin** → lonceng 🔔 → klik notifikasi *"Kazu foun …"* → tombol **Verifika** (paling bawah) → *"Status muda ona ba Verifikadu"*.
3. **Superadmin** → 🔔 *"… verifika ona husi Admin. Hein ita-nia aprovasaun"* → **Aprova** → *"Status muda ona ba Aprovadu"*.
4. Cek hasil:
   - **Dashboard** (Admin/Superadmin): angka Liquiçá bertambah.
   - **Portal Publik** http://127.0.0.1:8000/portal/ (tanpa login): angka Liquiçá bertambah. Di DEBUG langsung; di produksi maks. 10 menit (cache).
   - Teste penolakan (opsional): Admin klik **Rejeita** + alasan → Investigadór dapat notifikasi, bisa **Edita** dan kirim lagi.

## C. Cek data MASUK atau TIDAK

```bash
python manage.py cek_kazu                          # semua kasus 7 hari terakhir (web + HP)
python manage.py cek_kazu --kode SMKRE-LIQ-2026-00016
python manage.py cek_kazu --email teste.investigador@redebarai.org
```

Contoh hasil:
```
KÓDIGU                 HUSI STATUS     MUNISÍPIU    FOTO  INVESTIGADÓR         VERIFIKA           APROVA             PORTAL
SMKRE-LIQ-2026-00016   WEB  APPROVED   Liquiçá         0  teste.investigador   teste.admin        teste.superadmin   SIN
```

| Kolom | Arti |
|---|---|
| `HUSI` | `WEB` = form online · `HP` = app offline (lihat `docs/TESTE_OFFLINE.md`) |
| `STATUS` | `DRAFT` rascunho · `SYNCED` hein verifikasaun · `VERIFIED` · `APPROVED` · `COMPLETED` · `REJECTED` |
| `VERIFIKA` / `APROVA` | siapa yang klik Verifika / Aprova |
| `PORTAL` | `SIN` = tampil di portal publik (aprovadu + konsentimentu + tidak ditandai "la publika") |

## Masalah umum

| Gejala | Penyebab / solusi |
|---|---|
| Menu *Kazu Foun* tidak ada | Akun bukan Investigadór |
| "Ita seidauk iha munisípiu knaar" | Investigadór belum punya munisípiu → jalankan `teste_online` atau Admin isi di menu Utilizador |
| Kasus tersimpan sebagai rascunho, tidak terkirim | Ada kolom wajib kosong (postu, suku, GPS, tipe, deskripsi, konsentimentu) → pesan merah di form |
| GPS ditolak | Akurasi > 50 m atau di luar Timor-Leste → pakai Sensors di DevTools |
| Tombol Verifika tidak ada | Login sebagai Admin (Superadmin hanya **Aprova**, setelah Admin verifika) |
| Email notifikasi | Jika `.env` memakai `EMAIL_BACKEND=...console.EmailBackend` (default), email tampil di terminal `runserver`, tidak benar-benar dikirim. Untuk teste kirim sungguhan pakai `smtp.EmailBackend` + App Password Gmail |
