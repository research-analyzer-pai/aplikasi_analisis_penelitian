# Research Analyzer Professional v4.2
## SEM Inference & Diagnostics Edition

v4.2 melanjutkan v4.1 dan menambahkan modul analisis berbasis skor teramati:

1. **Mediation bootstrap**: model X → M → Y, efek a, b, c', c, efek tidak langsung ab, dan percentile confidence interval.
2. **Moderation bootstrap**: pemusatan skor X dan W, interaksi X×W, bootstrap CI, dan simple slopes.
3. **VIF diagnostics**: pemeriksaan multikolinearitas prediktor.
4. **Streamlit workspace**: tab baru `SEM Inference & Diagnostics v4.2`.

### Menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Pengujian
```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```

### Batasan metodologis
- Modul mediasi dan moderasi memakai skor teramati/komposit dan OLS; bukan CB-SEM, bukan PLS-SEM laten, dan bukan pengganti AMOS/lavaan/SmartPLS.
- Mediasi cross-sectional tidak membuktikan urutan temporal atau kausalitas.
- Percentile bootstrap bergantung pada kualitas data, ukuran sampel, spesifikasi model, dan jumlah replikasi.
- Kovariat dapat ditambahkan melalui API Python; UI saat ini menggunakan model dasar tanpa kovariat.
- Uji unit tidak menggantikan benchmark numerik terhadap perangkat lunak statistik tervalidasi atau pengujian end-to-end UI.
- Semua interpretasi dan keputusan model tetap menjadi tanggung jawab peneliti.
