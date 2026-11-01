# Research Analyzer Professional v4.1

**Advanced Quantitative & Qualitative Diagnostics Edition**

v4.1 melanjutkan v4.0 dan menambahkan:

1. **Reliability diagnostics** — Cronbach's alpha, corrected item-total correlation, dan alpha-if-deleted.
2. **Factorability screening** — Kaiser-Meyer-Olkin (KMO) dan Bartlett's test of sphericity.
3. **Qualitative evidence audit** — coding coverage, frekuensi kode, orphan coding IDs, dan daftar segmen yang belum terkoding.
4. **Streamlit workspace** — tab `Advanced Research Diagnostics v4.1`.

## Menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pengujian
```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```

## Batasan interpretasi
- Alpha tidak membuktikan unidimensionalitas atau validitas konstruk.
- KMO dan Bartlett hanya pemeriksaan kelayakan awal analisis faktor; penentuan jumlah faktor memerlukan dasar teori dan evaluasi lanjutan.
- Coding coverage bukan ukuran saturasi teoretis, kualitas tema, atau validitas temuan.
- Segmen yang belum terkoding harus ditinjau; tidak otomatis merupakan negative case.
- Mesin PLS-SEM terdahulu tetap prototipe eksploratif. Gunakan perangkat lunak tervalidasi dan laporkan prosedur estimasi secara transparan.
- Pengujian unit tidak sama dengan pengujian end-to-end antarmuka atau uji API langsung.
