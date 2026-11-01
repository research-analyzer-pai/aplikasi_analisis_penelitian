# Research Analyzer Professional v4.3
## CFA & CB-SEM Engine

### Fitur baru
- CR dan AVE dari standardized factor loadings yang diimpor.
- Cronbach's alpha dari peta konstruk-indikator yang ditentukan peneliti.
- HTMT matrix dari data indikator.
- Fornell-Larcker matrix dari AVE dan korelasi konstruk yang diimpor.
- Audit indeks fit (CFI, TLI, RMSEA, SRMR, GFI) menggunakan batas heuristik yang dapat dikonfigurasi melalui API.
- Generator sintaks lavaan dan eksekusi opsional melalui Rscript/lavaan.
- Integrasi tab `CFA & CB-SEM Engine v4.3` di Streamlit.

### Instalasi dan menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```
Untuk CB-SEM, instal R, paket R `lavaan`, dan pastikan `Rscript` tersedia pada PATH komputer yang menjalankan aplikasi.

### Pengujian
```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```

### Batasan
- CR/AVE dihitung dari loading terstandar yang diberikan peneliti; bukan estimasi CFA otomatis oleh modul Python.
- HTMT, alpha, dan Fornell-Larcker adalah diagnostik yang sensitif terhadap kualitas data dan spesifikasi konstruk.
- Ambang fit index bersifat heuristik dan harus dipertimbangkan sesuai estimator, ukuran sampel, kompleksitas model, dan literatur metodologis.
- Eksekusi CB-SEM memerlukan R/lavaan lokal; tidak diuji live pada lingkungan build ini jika R tidak tersedia.
- Model harus ditetapkan berdasarkan teori; aplikasi tidak menentukan model yang benar secara otomatis.
