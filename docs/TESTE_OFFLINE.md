# Teste App Offline di Lokal (laptop & HP)

Tujuan: memastikan kasus yang diisi **tanpa internet** benar-benar **masuk ke database** setelah sinkron.

## A. Persiapan (sekali)

```bash
cd SMKRE
source Env/bin/activate            # Windows: Env\Scripts\activate
python manage.py migrate
python manage.py setup_smkre
python manage.py teste_offline     # buat investigador teste + izin offline 7 hari
python manage.py runserver
```

`teste_offline` mencetak email + password teste (default `teste.offline@redebarai.org` / `Teste#Offline-2026`, munisípiu Liquiçá).
Opsi: `--email`, `--password`, `--munisipiu DIL`. Hanya jalan jika `DEBUG=True`.

## B. Teste di laptop (paling mudah — Chrome)

`localhost` dianggap aman oleh browser, jadi GPS, kamera, enkripsi dan service worker berfungsi tanpa HTTPS.

1. Buka **http://127.0.0.1:8000/sinkron/** → login dengan akun teste → buat **PIN 6 angka**.
2. Tekan **F12** → tab **Network** → ubah *No throttling* menjadi **Offline**.
3. Klik **Kazu Foun** → isi 6 langkah:
   - Langkah 1: GPS — di laptop izinkan lokasi. Jika akurasi laptop > 50 m, pakai DevTools → ⋮ → *More tools* → **Sensors** → *Location* → pilih/isi koordinat Timor-Leste (mis. -8.5874, 125.3412).
   - Langkah 5: foto memakai webcam laptop.
   - Langkah 6: centang **konsentimentu** → **Prontu**.
4. Muncul pesan *"Kazu rai ona iha HP (enkriptadu)…"* dan kasus berstatus **Hein Sinkron**.
5. (Opsional) tekan **F5** saat masih offline → app tetap terbuka → masukkan PIN → kasus masih ada.
6. Network → kembali ke **No throttling** (online) → sinkron otomatis → pesan *"Sinkron remata: 1 susesu"* dan kasus mendapat kode `SMKRE-LIQ-2026-xxxxx`.

## C. Cek data MASUK atau TIDAK

**Terminal:**
```bash
python manage.py cek_sinkron                 # kasus dari HP 7 hari terakhir
python manage.py cek_sinkron --email teste.offline@redebarai.org --loron 1
```
Contoh hasil:
```
KÓDIGU                   STATUS     FATIN                      GPS                    FOTO VÍDEO  INVESTIGADÓR / SINKRON
SMKRE-LIQ-2026-00015     SYNCED     Guguleur, Liquiçá          -8.587400,125.341200      1     0  teste.offline@redebarai.org · 29/09 14:25
Total 1 kazu husi HP · 1 kompletu
```
- `SYNCED` = data + evidénsia lengkap masuk, Admin sudah dinotifikasi.
- `PENDING` = data masuk tapi foto/video atau langkah "haruka" belum selesai → buka app di HP lalu **Sinkron** lagi (aman, tidak membuat duplikat).
- Tidak muncul sama sekali = belum sinkron (cek pesan error di app HP).

**Web:** login sebagai Admin → menu **Kazu** → kasus baru muncul dengan status *Hein Verifikasaun*; lonceng 🔔 berisi *"Kazu foun … husi …"*. Riwayat kasus menulis *"Sinkron husi HP"*.

## D. Teste di HP Android (satu jaringan WiFi dengan laptop)

Kamera/GPS butuh HTTPS. Untuk teste lokal, Chrome Android bisa diberi pengecualian:

1. Laptop: cari IP (mis. `192.168.1.10`), lalu di `.env` tambahkan IP itu ke `ALLOWED_HOSTS` dan jalankan:
   `python manage.py runserver 0.0.0.0:8000`
2. HP Android → Chrome → buka `chrome://flags` → cari **Insecure origins treated as secure** → isi `http://192.168.1.10:8000` → **Enabled** → Relaunch.
3. Buka `http://192.168.1.10:8000/sinkron/` → login → PIN.
4. Nyalakan **Mode Pesawat** → isi kasus (kamera HP asli, GPS asli — di luar ruangan agar ≤ 50 m) → Prontu.
5. Matikan Mode Pesawat → sinkron otomatis → cek di laptop: `python manage.py cek_sinkron`.

**iPhone:** tidak ada pengecualian seperti di atas → perlu HTTPS (server teste dengan domain + certbot, atau tunnel HTTPS). Di produksi (HTTPS) semua HP jalan normal.

## E. Mengulang teste dari awal

- Di HP/laptop: app → *Haluha PIN? Hamoos dadus iha HP* (menghapus data lokal), atau DevTools → Application → *Clear site data*.
- Izin offline baru: jalankan lagi `python manage.py teste_offline`.

## Masalah umum

| Gejala | Penyebab / solusi |
|---|---|
| "Autorizasaun offline la ativu" saat login | Jalankan `teste_offline` atau Admin beri izin di menu *Offline* |
| Tombol *Kazu Foun* abu-abu | Izin offline habis → hanya bisa sinkron; beri izin baru |
| GPS tidak ≤ 50 m | Di laptop pakai Sensors (DevTools); di HP keluar ruangan |
| "Kazu ne'e kria iha li'ur períodu autorizasaun" | Kasus dibuat saat izin belum/sudah tidak berlaku, atau jam HP salah |
| Kamera tidak terbuka | Izinkan kamera di pengaturan browser; tutup aplikasi lain yang memakai kamera |
| Status `PENDING` di `cek_sinkron` | Buka app → **Sinkron** lagi |
