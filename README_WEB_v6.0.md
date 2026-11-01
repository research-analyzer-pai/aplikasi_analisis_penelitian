# Research Analyzer Professional Web v6.0

## Status
Paket aplikasi web berbasis Streamlit. Dapat dijalankan melalui browser pada komputer lokal atau di-deploy ke hosting yang mendukung Python/Docker. **Paket ini belum di-hosting dan belum memiliki URL publik.**

## Fitur web v6.0
- Antarmuka terpadu yang mempertahankan modul analisis v5.0.
- Workspace: ekspor/impor paket proyek ZIP berisi dataset aktif.
- Developer Studio: struktur extension, contoh modul, dan alur pengujian.
- Opsional gerbang kata sandi bersama melalui variabel lingkungan `RA_WEB_PASSWORD`.
- Dockerfile dan Procfile untuk membantu deployment.

## Jalankan lokal
1. Instal Python 3.11.
2. Ekstrak ZIP.
3. Buat virtual environment:
   `python -m venv .venv`
4. Aktifkan environment, lalu:
   `pip install -r requirements.txt`
5. Jalankan:
   `streamlit run app.py`
6. Buka alamat lokal yang ditampilkan Streamlit, biasanya `http://localhost:8501`.

## Deploy melalui Docker
`docker build -t research-analyzer-web .`
`docker run --rm -p 8501:8501 -e RA_WEB_PASSWORD='ganti-dengan-rahasia-kuat' research-analyzer-web`

## Deploy ke layanan hosting
Unggah folder proyek ke repositori Git, lalu hubungkan repositori ke layanan hosting Python/Docker yang mendukung Streamlit. Gunakan:
- Start command: `streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true`
- Python: 3.11
- Environment variable `RA_WEB_PASSWORD`: opsional untuk satu kata sandi bersama.

## Pengembangan modul
- Tambahkan modul Python di `extensions/`.
- Tulis unit test di `tests/`.
- Extension tidak dieksekusi otomatis. Integrasikan secara eksplisit setelah code review.
- Jalankan `python -m unittest discover -s tests -v`.

## Batasan keamanan dan operasional
- Password gate yang disediakan adalah gerbang kata sandi bersama sederhana, bukan sistem akun individual, RBAC, atau autentikasi enterprise.
- Data proyek berada dalam memori sesi saat aplikasi berjalan. Paket ini belum memakai database permanen, object storage, backup otomatis, atau isolasi tenant.
- Untuk penggunaan publik/produksi, tambahkan autentikasi individual, HTTPS pada hosting, database, kontrol akses, audit log, enkripsi dan kebijakan retensi.
- Jangan unggah data sensitif atau identitas informan tanpa dasar etik dan perlindungan yang memadai.
- Modul SEM/PLS dan metode lain tetap mengikuti batasan metodologis yang dijelaskan pada dokumentasi v5.0. Hasil harus diverifikasi peneliti.

## Fitur yang dipertahankan
Seluruh modul, dokumentasi, data contoh, dan unit tests dari paket v5.0 disertakan. Versi web ini menambahkan lapisan workspace dan pengembangan; tidak mengubah hasil analisis menjadi otomatis benar.
