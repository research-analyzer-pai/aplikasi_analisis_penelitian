# Research Analyzer Professional v5.1 — Multi-format input

Versi 5.1 mempertahankan fitur v5.0 dan menambahkan input data inti multi-format.

## Format utama
- Kuantitatif: `.xlsx`, `.xls`, `.csv` pada tab **Data**.
- Kualitatif: `.docx`, `.pdf`, `.txt`, `.md`, serta `.xlsx`, `.xls`, `.csv` pada tab **Kualitatif**.
- Untuk Excel, pilih worksheet yang akan diimpor.
- Untuk spreadsheet kualitatif, sediakan kolom teks bernama `text`, `teks`, `transcript`, `transkrip`, `kutipan`, atau `isi`.

## Menjalankan lokal
1. Ekstrak seluruh isi ZIP.
2. Gunakan Python 3.10 atau lebih baru.
3. Instal dependensi: `pip install -r requirements.txt`.
4. Jalankan: `streamlit run app.py` atau klik `run_web.bat` pada Windows.

## Deployment Streamlit Community Cloud
- Repository harus berisi seluruh isi paket pada root.
- Branch: `main` (atau branch yang benar-benar digunakan).
- Main file path: `app.py`.
- Setelah commit/push, Streamlit Community Cloud akan membangun ulang aplikasi.

## Batasan ekstraksi
- PDF hasil scan/gambar memerlukan OCR terlebih dahulu.
- PDF teks dan DOCX tetap perlu diperiksa peneliti sebelum proses coding.
- Impor Excel/CSV tidak otomatis menentukan skala, konstruk, atau peran variabel; lakukan validasi dan pemetaan oleh peneliti.
- Beberapa tab analisis lanjutan masih menerima CSV secara khusus sesuai skema modul masing-masing. Tab Data dan Kualitatif adalah alur impor utama yang kini mendukung multi-format.

## Catatan metodologis
Output analisis merupakan bantuan analitik. Keputusan metodologis, interpretasi, validitas instrumen, dan pelaporan akhir tetap menjadi tanggung jawab peneliti.
