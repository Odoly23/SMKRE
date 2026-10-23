# Model Kazu — estrutura no regra (ba developer)

Model kazu fahe ba file ki'ik iha `kazu/models/` (pakote). Import hanesan uluk:
`from kazu.models import Kazu, KazuEviksaun, VERIFIED`.

| File | Konteúdu |
|---|---|
| `opsaun.py` | Status no choices hotu (konstante) |
| `kazu.py` | `Kazu` — tabela sentrál: identifikasaun, status, fatin administrativu + GPS, urjente, auditoria. `KazuSequence` (kódigu RbR-MUN-TINAN-NNNN) |
| `seksaun.py` | Seksaun OneToOne: `KazuFatin` (enderesu, luan, poligon), `KazuEntidade`, `KazuPopulasaun`, `KazuEviksaun`, `KazuPortavos` |
| `afetadu.py` | Lista laran: `UmaKainAfetada`, `InsidenteEviksaun`, `AtorEnvolvidu` |
| `evidensia.py` | `Evidensia` (foto, vídeo, dokumentu) |
| `segimentu.py` | `KazuSegimentu` (tribunál, notifikasaun, status — OneToOne), `KazuAkompanamentu` |
| `importa.py` | `KazuImport` (Excel / Airtable) |
| `historia.py` | `KazuHistoria` (se, bainhira, razaun) |

## Regra

1. **Tabela `Kazu` ki'ik.** Kampu ne'ebé uza iha buka/filtru/mapa/kódigu (munisípiu, status, GPS, urjente) de'it mak hela iha `Kazu`.
   Detalla seluk tama iha **seksaun OneToOne** (`related_name` = naran seksaun).
2. **Naran kampu úniku.** Kampu seksaun mosu mós iha `Kazu` hanesan *property* (lee/hakerek):
   `kazu.eviksaun_akontese = 'SIN'; kazu.save()` → rai iha `KazuEviksaun`. Formuláriu, app offline, sinkron no
   Airtable uza naran ne'e — keta troka naran kampu ne'ebé iha ona.
3. **ORM uza naran relasaun** ba kampu seksaun:
   `Kazu.objects.filter(eviksaun__eviksaun_akontese='SIN')`, `.order_by('fatin__rai_luan')`.
   Lista ho kampu seksaun barak: `.select_related(*SEKSAUN_REL)` (query ida de'it).
4. **Kazu la iha liña seksaun** → property fó valór default (mamuk). Liña kria automátiku bainhira hakerek.
5. Field iha import/export jenériku: `Kazu.kampu('naran')` (buka iha Kazu ka seksaun).

## Aumenta kampu foun

- **Iha seksaun ne'ebé iha ona** (ex. eviksaun): aumenta field iha `seksaun.py` → `python manage.py makemigrations kazu`.
  Formuláriu web hetan automátiku (`KAMPU_SEKSAUN_FORM` iha `kazu/forms.py`); aumenta iha layout (`helper_*`), app offline
  (`sinkron/templates/sinkron/app.html` + `KAMPU_RBR` iha `smkre_offline.js`) no `KAZU_CAMPO_RBR` (sinkron) se presiza.
- **Seksaun foun** (ex. `KazuKompensasaun`):
  1. Kria classe iha `seksaun.py` herda `SeksaunBase`, ho
     `kazu = models.OneToOneField(Kazu, on_delete=models.CASCADE, primary_key=True, related_name='kompensasaun')`.
  2. Rejistu iha `SEKSAUN` (dict iha okos `seksaun.py`).
  3. `makemigrations kazu` + test.
- **Lista (barak kada kazu)**: `ForeignKey('kazu.Kazu', related_name=...)` hanesan `UmaKainAfetada`.

## Migrasaun dadus

`kazu/migrations/0014_seksaun_onetoone.py` muda kampu husi `Kazu` ba seksaun (bele fila: `migrate kazu 0013`).
Molok migrasaun iha server: halo backup baze dadus.
