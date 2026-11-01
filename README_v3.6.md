# Research Analyzer Professional v3.6

Versi ini mempertahankan aplikasi v3.5 dan menambahkan modul kualitatif yang dapat diaudit.

## Fitur
- Semantic coding multilingual opsional (`sentence-transformers`). Model default: `paraphrase-multilingual-MiniLM-L12-v2`.
- Cohen's Kappa untuk dua coder dengan unit coding yang disejajarkan.
- Tracker enam fase analisis tematik refleksif Braun & Clarke.
- Validasi codebook hierarkis dan deteksi siklus parent-child.
- Matriks triangulasi tema, sumber, dan teknik.
- Daftar segmen belum terkoding untuk diperiksa sebagai kemungkinan kasus negatif atau bukti terlewat.

## Instalasi
Jalankan `pip install -r requirements.txt`. Untuk semantic coding opsional jalankan `pip install -r requirements_v36_optional.txt`.
Model embedding diunduh pada penggunaan pertama; siapkan model lokal jika bekerja offline.

## Catatan metodologis
Saran embedding bukan keputusan coding final. Cohen's Kappa mengukur kesepakatan dua coder, bukan validitas tema. Braun–Clarke disediakan sebagai tracker proses refleksif; bukan prosedur otomatis open-axial-selective coding. PLS-SEM tetap prototipe eksploratif.
