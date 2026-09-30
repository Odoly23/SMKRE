# Wilayah — Diploma Ministerial N.º 31/2026

Fonte: *Jornal da República*, Série I, N.º 26 D (3 Julho 2026) — "Reconhecimento dos Sucos e das Aldeias":
**472 suco, 2250 aldeia**, anexo I–XIV (kada munisípiu).

Rezultadu (iha `custom/data/wilayah/`):

| File | Konteúdu |
|---|---|
| `wilayah_dm31_2026.xlsx` | Aba *Lee-uluk*, *Suku* (VERIFIKA kór-mean), *Aldeia*, *Postu* |
| `postu_dm31_2026.csv` | 71 postu (65 sistema + 6 foun: Quelicai Antigu, Matebian, Hatulia A/B, Loré, Loes) |
| `suku_dm31_2026.csv` | 472 suku ho postu_code (57 mamuk = VERIFIKA) |
| `aldeia_dm31_2026.csv` | 2250 aldeia ho suku_code |

## Oinsá hari'i fali (se iha PDF foun)

```bash
pip install pymupdf openpyxl
python tools/wilayah_dm31/1_parse_pdf.py SERIE_I_NO_26_D.pdf /tmp/w.json
python tools/wilayah_dm31/2_metodu_pt.py /tmp/w.json /tmp/w_pt.json
python tools/wilayah_dm31/3_metodu_linha.py /tmp/w.json /tmp/w_linha.json
python tools/wilayah_dm31/4_exporta.py /tmp/w_pt.json /tmp/w_linha.json custom/data/postu.csv custom/data/wilayah
```

## Oinsá funsiona (no limitasaun)

- **Aldeia → Suku**: kolun ofisiál "NO ALDEIA" + pozisaun liña (suco iha klaran nia bloku). Validasaun: 469/469 NO ALDEIA
  hanesan ho liña tabela; 3 suco (Acubilitoho, Betulau, Bereleu) kolun mamuk iha PDF → konta husi liña.
- **Salah-ketik PDF**: Maubaralissa hakerek "354" (loos 344) → orden tuir pozisaun iha dokumentu.
- **Suku → Postu**: label postu iha PDF hakerek dala ida deit, iha klaran sel ne'ebé kruza página. Metodu rua
  (koordenada pt no indise liña); **postu prenxe deit bainhira metodu rua konkorda** (415 suku).
  57 suku = **VERIFIKA**: 33 tanba label postu la iha PDF (Aileu: Laulara/Lequidoe/Remexio; Lautém: Lautém/Moro),
  24 iha fronteira entre postu rua (sujestaun rua iha kolun `sujestaun`).
- Naran PDF (MAIÚSKULA) → "Titulu" (ex. `SUCO LIURAI` → `Suco Liurai`). Naran hanesan (ex. Iliomar, Maina) PDF la hakerek I/II.
