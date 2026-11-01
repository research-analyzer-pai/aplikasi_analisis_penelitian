# Research Analyzer Professional v3.9

## Fokus
Manuscript & APA Intelligence: pemeriksaan awal konsistensi sitasi, daftar pustaka, struktur manuskrip, abstrak, dan kata kunci.

## Modul baru
`manuscript_intelligence_v39.py`

Contoh:
```python
from manuscript_intelligence_v39 import audit_apa_consistency, manuscript_readiness
report = audit_apa_consistency(manuscript_text, reference_entries)
checklist = manuscript_readiness(manuscript_text, abstract_max_words=250)
```

## Menjalankan aplikasi utama
```bash
pip install -r requirements.txt
streamlit run app.py
```

Modul v3.9 disediakan sebagai fungsi Python yang dapat digunakan bersama modul sebelumnya. Antarmuka Streamlit lengkap dan koneksi Crossref live belum diimplementasikan pada rilis ini.
