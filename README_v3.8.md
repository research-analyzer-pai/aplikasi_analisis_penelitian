# Research Analyzer Professional v3.8

## Fokus
Evidence-grounded academic reporting untuk membantu menyiapkan draf Bab IV–V dari hasil analisis yang telah diimpor.

## Modul baru
- `academic_reporting_v38.py`: audit format hasil SEM, tabel hipotesis, kerangka Bab IV, kerangka Bab V, ekspor DOCX.
- Seluruh modul dan fungsi v3.7 dipertahankan.

## Contoh penggunaan Python
```python
import pandas as pd
from academic_reporting_v38 import audit_sem_results, make_chapter_iv_draft
raw = pd.read_csv('sem_results.csv')
audited = audit_sem_results(raw)
print(audited)
chapter_iv = make_chapter_iv_draft(audited, 'Konteks penelitian...', 'Estimator dan prosedur...')
```

## Menjalankan aplikasi
```bash
pip install -r requirements.txt
streamlit run app.py
```

Modul pelaporan v3.8 dapat dipanggil dari Python; integrasi tab antarmuka penuh perlu diuji pada instalasi Streamlit lokal. Draf wajib ditinjau peneliti. Gunakan kutipan anonim dan data yang telah disetujui secara etik.
