# Research Analyzer Professional v5.0 — Paket Deployment Web

Paket ini berisi aplikasi Streamlit v5.0 dan konfigurasi dasar untuk deployment.

## A. Cara paling mudah: Streamlit Community Cloud

1. Ekstrak seluruh isi ZIP ini.
2. Unggah **seluruh isi folder** ke repository GitHub (bukan ZIP sebagai satu file).
3. Pastikan `app.py` dan `requirements.txt` berada di direktori utama repository.
4. Buka https://share.streamlit.io/ dan masuk menggunakan akun GitHub.
5. Pilih **Create app**.
6. Pilih repository, branch (biasanya `main`), dan Main file path: `app.py`.
7. Klik **Deploy** dan tunggu proses instalasi dependensi.
8. Jika berhasil, Streamlit akan memberikan URL `*.streamlit.app`.

## B. Jika repository sudah berisi file aplikasi

Bandingkan dengan paket ini. Pastikan setidaknya:
- `app.py`
- `requirements.txt`
- semua modul `.py` yang diimpor oleh `app.py`
- folder `tests/`, `data/`, dan `docs/` (disarankan)
- folder `.streamlit/` (konfigurasi tampilan)

Jangan menghapus modul yang diimpor aplikasi.

## C. Pemeriksaan awal

Dari root folder, jalankan:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## D. Catatan keamanan dan metodologis

- Jangan memasukkan password, token GitHub, API key, atau data identitas partisipan ke repository publik.
- Jika memakai API key, simpan melalui menu Secrets pada layanan hosting, bukan di kode.
- Aplikasi ini adalah alat bantu analisis. Hasil PLS-SEM prototipe, rekomendasi coding, dan narasi laporan harus ditelaah peneliti.
- Deployment belum berarti validasi statistik atau audit keamanan untuk penggunaan data sensitif.
- Gunakan repository privat bila memuat data atau materi yang tidak untuk publik.
