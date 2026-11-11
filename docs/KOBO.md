# Koneksaun KoboToolbox → SIBAR-RbR

SIBAR-RbR **tarik** (pull) submission husi KoboToolbox no kria Kazu automátiku, liuhusi
pipeline import ne'ebé hanesan ho import Excel (validasaun, lokalizasaun, GPS aproksimadu,
cek duplikadu, istória no notifikasaun). La presiza webhook públiku.

## 1. Prepara iha KoboToolbox
1. Account → Security → **API token**: kopia token (string naruk).
2. Loke projetu/formuláriu → URL iha `.../forms/<ASSET_UID>/...` → kopia **ASSET_UID**
   (ex. `aBcDeF123...`).

## 2. Konfigurasaun iha `.env` (servidor)
```
KOBO_BASE_URL=https://kf.kobotoolbox.org      # ka servidor Kobo organizasaun nian
KOBO_TOKEN=<token API husi Kobo>              # SEGREDU — labele iha kódigu/git
KOBO_ASSET_UID=<ASSET_UID formuláriu>
```

## 3. Hadia mapeamentu field (importante!)
Naran pergunta iha formuláriu Kobo imi-nian PRESIZA mapeia ba kolun SIBAR.
1. Haree submission ida:
   ```
   python manage.py sync_kobo --amostra
   ```
   (hatudu JSON submission ida — haree naran pergunta loloos.)
2. Hadia `MAPA` no `MAPA_GPS` iha **`kazu/kobo.py`** tuir naran pergunta sira ne'e.
   Kolun SIBAR importante: `munisipiu`, `postu`, `suku`, `aldeia`, `data_relatoriu`,
   `tipu_konflitu`, `deskrisaun`, GPS (geopoint), `konsentimentu`, `uma_kain`, `mane`, `feto`.

## 4. Testa (la kria dadus)
```
python manage.py sync_kobo --dry-run
```
Hatudu total, foun, sala, no amostra. Hadia MAPA to'o kazu ne'ebé ok.

## 5. Kria kazu
```
python manage.py sync_kobo
```
Kazu foun mosu ho status **Hein Verifikasaun** (hanesan sinkron husi HP) → Admin verifika,
Superadmin aprova. Submission ne'ebé import ona la import fali (dedup liuhusi `kobo_uuid`).

## 6. Automátiku (loron-loron)
PythonAnywhere → **Tasks** (ka cron):
```
cd ~/SMKRE && ~/.virtualenvs/smkre-env/bin/python manage.py sync_kobo >> ~/SMKRE/logs/kobo.log 2>&1
```

## Nota PythonAnywhere (importante)
Konta **gratuitu** PythonAnywhere só bele konekta ba host iha lista branku (whitelist).
Se `sync_kobo` hetan erru koneksaun, `kf.kobotoolbox.org` karik la iha whitelist → presiza:
- husu PythonAnywhere atu aumenta host ne'e, ka
- uza konta paga (outbound livre), ka
- uza webhook (Kobo "REST Services" push mai SIBAR) — maibé presiza endpoint públiku.

## Seguransa
- Token Kobo rai iha `.env` de'it (segredu).
- Kazu husi Kobo la'o liuhusi validasaun hanesan import Excel; dadus sala → sala (la kria).
- Formula injection iha ekspor Excel protezidu ona (haree config/excel_seguru.py).
